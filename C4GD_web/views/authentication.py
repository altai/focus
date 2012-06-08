# coding=utf-8
import json
import requests
import datetime

from flask import g, session, request, current_app, render_template
from flask import flash, redirect, url_for
from flaskext import principal

from C4GD_web import app, mail
from C4GD_web.utils import obtain_scoped, keystone_obtain_unscoped,\
    neo4j_api_call, create_hash_from_data, create_hashed_password, \
    user_tenants_list, get_keystone_user_by_username

from .forms import get_login_form, PasswordRecoveryRequest

from flaskext.mail import Message

from C4GD_web.clients import clients
from C4GD_web.exceptions import GentleException

import MySQLdb

def authenticate_user(odb_user, password):
    """
    Checks if user exists in ODB
    Obtains tokens from keystone and storing them in session
    """
    try:
        odb_user = neo4j_api_call('/users',{
            "email": odb_user['email']
        }, 'GET')[0]
    except KeyError, GentleException:
        flash('user does not exists in ODB', 'error')
        return False
    
    success, unscoped_token_data = keystone_obtain_unscoped(
        odb_user['username'], password)
    if success:
        session['user'] = odb_user
        g.is_authenticated = True
        flash('You were logged in successfully.', 'success')
        session["keystone_unscoped"] = unscoped_token_data
        user_tenants = user_tenants_list(get_keystone_user_by_username(odb_user['username']))
        session['tenants'] = user_tenants
        if 'keystone_scoped' not in session:
            session['keystone_scoped'] = {}
        # this is not obvious but useful here
        for tenant in user_tenants:
            obtain_scoped(tenant['id'])
        principal.identity_changed.send(
            app,
            identity=principal.Identity(
                session["keystone_unscoped"]['access']['user']['id']))
    return success


def register_user(username, email, password, role):
    """
        Temporary have to register user in ODB and add a user into
        keystone db using keystoneclient
    """
    def register_in_keystone():
        """
        TODO(spugachev):
        convert all requests here to keystoneclient's calls
        """
        try:
            new_keystone_user = clients.keystone.users.create(username, password, email)
            
            if role != 'user':
                all_roles = clients.keystone.roles.list()
                for r in all_roles:
                    if r.name == role:
                        clients.keystone.roles.add_user_role(
                            new_keystone_user, r, 
                            tenant=app.config['KEYSTONE_CONF']['admin_tenant_id'])
                        break
        except Exception, e:
            raise Exception("Registration fail", e.message)
        return True
                
    
    def register_in_ODB():
        """
        API 'create_user' call to ODB, then read new user from ODB and returns it.
        """
        # new user
        new_user = neo4j_api_call('/users', {
            "login": "",
            "username": username,
            "email": email,
            "passwordHash": create_hashed_password(password),
        }, 'POST')
        
        
        # return fresh user
        user = neo4j_api_call('/users',{
            "email": email
        }, 'GET')[0]
        return user
     
    keystone_success = register_in_keystone()
    
    if keystone_success:
        user = register_in_ODB()
        return user
    else:
        return None


@app.route('/login/', methods=['GET', 'POST'])
def login():
    """
    Log user in.

    Openstack KEystone component is our prime authentication source.
    Currently on login we are trying to obtain an unscoped token.
    On success we store the response in session as "unscoped_token".
    This piece of data is our authentication marker.
    If this is missing the user is not authenticated anymore.

    As a shortcut to save further work we instantly ask for scoped tokens
    for every tenant the user belongs to. These data is not important,
    it can be re-queried at any given moment.
    """
    form = get_login_form()()
    if form.validate_on_submit():
        try:
            user = neo4j_api_call('/users', {'email': form.username.data},'GET')[0]
        except KeyError, GentleException:
            flash("User doesn't exists, code: 2", 'error')
            return {'form': form}
        if user['passwordHash'] != create_hashed_password(form.password.data):
            flash("Wrong username/password, code: 3", 'error')
            return {'form': form}
        if authenticate_user(user, form.password.data):
            return redirect(form.next.data)
    return {'form': form}


@app.route('/logout/')
def logout():
    """
    Log user out.

    Instead of removing authentication marker only clear whole session.
    """
    session.clear()
    flash('You were logged out', 'success')
    return redirect(url_for(current_app.config['DEFAULT_NEXT_TO_LOGOUT_VIEW']))


@app.route('/password_recovery_finish/<recovery_hash>/', methods=['GET'])
def password_recovery_finish(recovery_hash):
    """
    This will be called after user clicked link in email.
    """
    id, email, hash, complete = get_recovery_request_by_hash(recovery_hash)
    if complete == 1:
        flash('Password recovery token is expired', 'error')
        return redirect('/')
    odb_user = neo4j_api_call('/users',{"email": email}, 'GET')[0]
    new_hash = create_hash_from_data(hash)
    # set trash password in keystone
    keystone_user = get_keystone_user_by_username(odb_user['username']) 
    clients.keystone.users.update_password(keystone_user, new_hash)
    # set trash password in odb
    neo4j_api_call('/users',{
        'id': odb_user['id'],
        'login': odb_user['login'],
        'username': odb_user['username'],
        'email': odb_user['email'],
        'passwordHash': create_hashed_password(new_hash)}, 
        'PUT')
    # send trash password back to user
    msg = Message('Password recovery', recipients=[odb_user['email']])
    msg.body = render_template('RecoveryPasswordFinishEmail/body.txt', 
                               new_pass=new_hash)
    try:
        mail.send(msg)
        flash('New password was sent to you', 'success')  
    except Exception, e:
        flash('SMTP error', 'error')
    return redirect('/')


@app.route('/password_recovery_request/', methods=['GET', 'POST'])
def password_recovery_request():
    """
    Shows a form to user and allows to request password dropping via email
    Recovery tokens are stored in local MySQL db 'invitations'
    """
    form = PasswordRecoveryRequest()
    if form.validate_on_submit():
        # check if user exasts in database
        try:
            user = neo4j_api_call('/users',{"email": form.email.data}, 'GET')[0]
        except KeyError, GentleException:
            flash('User with that email "%s" is not registered' % form.email.data, 
                  'error')
            return {}
        hash = create_hash_from_data(form.email.data)
        recovery_link = "http://%s%s" % (request.host, 
            url_for('password_recovery_finish', recovery_hash=hash))
        save_recovery(form.email.data, hash, 0)
        msg = Message('Password recovery', recipients=[form.email.data])
        msg.body = render_template('RecoveryPasswordEmail/body.txt', 
                                   recovery_link=recovery_link)
        try:
            mail.send(msg)
            flash('Recovery request was sent successfully', 'info')  
        except Exception, e:
            flash('SMTP error', 'error')
    return {'form': form}

from invitations.row_mysql_queries import save_recovery , \
    get_recovery_request_by_hash
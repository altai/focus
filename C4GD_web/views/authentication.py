# coding=utf-8
import json
import requests

from flask import g, session, request, current_app
from flask import flash, redirect, url_for, jsonify

from C4GD_web import app
from C4GD_web.utils import keystone_get, obtain_scoped, keystone_obtain_unscoped,\
    neo4j_api_call, create_hash_from_data

from .forms import get_login_form

import MySQLdb

def authenticate_user(user, password):
    success, unscoped_token_data = keystone_obtain_unscoped(
        user['username'], password)
    if success:
        session['user'] = user
        g.is_authenticated = True
        flash('You were logged in successfully.', 'success')
        session["keystone_unscoped"] = unscoped_token_data
        tenants = keystone_get('/tenants')
        session['tenants'] = tenants
        if 'keystone_scoped' not in session:
            session['keystone_scoped'] = {}
        # this is not obvious but useful here
        for tenant in tenants['tenants']['values']:
            obtain_scoped(tenant['id'])
    return success


def register_user(username, email, password, role):
    """
        Temporary have to register user in ODB and in manually add a user into
        keystone db.
    """
    def register_in_keystone():
        adm_keystone_url = current_app.config['KEYSTONE_URL'].replace('5000', '35357')
        
        # obtain admin unscoped token
        request_data = json.dumps({
            'auth': {
                'passwordCredentials': {
                    'username': app.config['ADMIN_KEYSTONE_USERNAME'],
                    'password': app.config['ADMIN_KEYSTONE_PASSWORD']
                    },
                }
        })
        response = requests.post(
            '%s/tokens' % adm_keystone_url,
            data=request_data,
            headers = {'content-type': 'application/json'})
        value = getattr(response, 'text')
        admin_auth_token = json.loads(value) if value != '' else ''
        
        if admin_auth_token is not None:
            
            # create user in keystone
            url = adm_keystone_url + '/users'
            headers = {'Content-Type': 'application/json',
                       'X-Auth-Token': admin_auth_token['access']['token']['id']}
            response = requests.post(
                url, 
                data=json.dumps({"user": {"name": username,
                   "password": password,
                   "tenantId": None,
                   "email": email,
                   "enabled": True}}), 
                headers=headers)
            new_user = json.loads(response.content)['user']
            
            # create role
            if role != 'user':
                url = adm_keystone_url + '/OS-KSADM/roles'
                response = requests.get(
                    url,
                    headers=headers,
                )
                roles = json.loads(response.content)['roles']['values']
                role_id = None
                for r in roles:
                    if r['name'] == role:
                        role_id = r['id']
                        break
                
                
                url = adm_keystone_url + '/users/%s/roles/OS-KSADM/%s' % (308, role_id)
                response = requests.put(
                    url,
                    headers=headers,
                )


                conn = MySQLdb.connect(
                    host=app.config['RW_DB_HOST'], 
                    user=app.config['RW_DB_USER'], 
                    passwd=app.config['RW_DB_PASS'], 
                    db=app.config['RW_DB_NAME'])
                cursor = conn.cursor()
                
                query = "INSERT INTO keystone.user_roles SET "+\
                    "user_id=%s," % new_user['id'] +\
                    "role_id=%s;" % role_id
                cursor.execute(query) 
                conn.commit()
                
            
            return True
        return False
                
    
    def register_in_ODB():
    # new user
        new_user = neo4j_api_call('/users', {
            "login": "",
            "username": username,
            "email": email,
            "passwordHash": create_hash_from_data(password),
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
        except KeyError:
            flash("User doesn't exists, code: 2", 'error')
            return {'form': form}
        if user['passwordHash'] != create_hash_from_data(form.password.data):
            flash("Wrong username/password, code: 3", 'error')
            return {'form': form}
        if authenticate_user(user, form.password.data):
            return redirect(form.next.data)
        else:
            flash('Wrong username/password, code: 3', 'error')
    return {'form': form}


@app.route('/logout/')
def logout():
    """
    Log user out.

    Instead of removing authentication merker only clear whole session.
    """
    session.clear()
    flash('You were logged out', 'success')
    return redirect(url_for(current_app.config['DEFAULT_NEXT_TO_LOGOUT_VIEW']))

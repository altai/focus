# coding=utf-8
# TODO(apugachev) to 'main' blueprint
import sys
import uuid

import flask
from flaskext import mail
from flaskext import principal

import C4GD_web
from C4GD_web import clients
from C4GD_web import exceptions
from C4GD_web import utils

from C4GD_web.views import forms


@C4GD_web.app.route('/login/', methods=['GET', 'POST'])
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
    form = forms.get_login_form()()
    if form.validate_on_submit():
        # TODO(apugachev) inline authenticate_user here
        # it must not be used anywhere else
        try:
            odb_user = utils.neo4j_api_call('/users', {
                "email": form.email.data
            }, 'GET')[0]
        except KeyError:
            # NOTE(apugachev)odb does not the email
            pass
        else:
            try:
                is_password_valid = odb_user['passwordHash'] == \
                    utils.create_hashed_password(form.password.data)
            except UnicodeEncodeError:
                # NOTE(apugachev) md5 digest does not work with unicode
                # and the password can't be unicode right now
                pass
            else:
                if is_password_valid:
                    # NOTE(apugachev)
                    # odb username is Keystone user name
                    # password is the same as Keystone password
                    success, unscoped_token = \
                        utils.keystone_obtain_unscoped(
                        odb_user['username'], form.password.data)
                    if success:
                        flask.session['user'] = odb_user
                        flask.g.is_authenticated = True
                        flask.flash(
                            'You were logged in successfully.',
                            'success')
                        flask.session['keystone_unscoped'] = unscoped_token
                        user_tenants = utils.user_tenants_list(
                            utils.get_keystone_user_by_username(
                                odb_user['username']))
                        flask.session['tenants'] = user_tenants
                        # NOTE(apugachev)
                        # Principal identity name is Keystone user id
                        principal.identity_changed.send(
                            C4GD_web.app,
                            identity=principal.Identity(
                                flask.session['keystone_unscoped'][
                                    'access']['user']['id']))
                        return flask.redirect(form.next.data)
        # required to wipe artifacts of unsuccessful attempts
        flask.session.clear()
        flask.flash('Wrong email/password.', 'error')
    return {'form': form}


@C4GD_web.app.route('/logout/')
def logout():
    """
    Log user out.

    Instead of removing authentication marker only clear whole session.
    """
    flask.flash('You were logged out', 'success')
    for key in flask.session.keys():
        if key != '_flashes':
            del(flask.session[key])
    return flask.redirect(flask.url_for(
            flask.current_app.config['DEFAULT_NEXT_TO_LOGOUT_VIEW']))


@C4GD_web.app.route(
    '/password_recovery_finish/<recovery_hash>/', methods=['GET'])
def password_recovery_finish(recovery_hash):
    """
    This will be called after user clicked link in email.
    """
    try:
        id, email, hash_code, complete = \
            row_mysql_queries.get_recovery_request_by_hash(recovery_hash)
    except TypeError:
        # db returns None
        flask.abort(404)
    if complete == 1:
        flask.flash('Password recovery token is expired', 'error')
        return flask.redirect(flask.url_for('dashboard'))
    odb_user = utils.neo4j_api_call('/users', {"email": email}, 'GET')[0]
    new_hash = str(uuid.uuid4())
    # set trash password in keystone
    keystone_user = utils.get_keystone_user_by_username(odb_user['username'])
    clients.clients.keystone.users.update_password(keystone_user, new_hash)
    # set trash password in odb
    utils.neo4j_api_call('/users', {
        'id': odb_user['id'],
        'login': odb_user['login'],
        'username': odb_user['username'],
        'email': odb_user['email'],
        'passwordHash': utils.create_hashed_password(new_hash)},
        'PUT')
    # send trash password back to user
    msg = mail.Message('Password recovery', recipients=[odb_user['email']])
    msg.body = flask.render_template('RecoveryPasswordFinishEmail/body.txt',
                               new_pass=new_hash)
    C4GD_web.mail.send(msg)
    flask.flash('New password was sent to you', 'success')
    return flask.redirect(flask.url_for('dashboard'))


#TODO(apugachev) looks like invite function, the same template, refactor
@C4GD_web.app.route('/password_recovery_request/', methods=['GET', 'POST'])
def password_recovery_request():
    """Start password recovery process.

    Shows a form to user and allows to request password dropping via email
    Recovery tokens are stored in local MySQL db 'invitations'
    """
    form = forms.PasswordRecoveryRequest()
    if form.validate_on_submit():
        # check if user exasts in database
        try:
            utils.neo4j_api_call(
                '/users', {"email": form.email.data}, 'GET')[0]
        except (KeyError, exceptions.GentleException):
            flask.flash(
                'User with that email "%s" is not registered.' %\
                    form.email.data,
                'error')
            exc_type, exc_value, traceback = sys.exc_info()
            flask.current_app.log_exception((exc_type, exc_value, traceback))
        else:
            hash_code = str(uuid.uuid4())
            recovery_link = "http://%s%s" % (flask.request.host,
                flask.url_for(
                    'password_recovery_finish', recovery_hash=hash_code))
            row_mysql_queries.save_recovery(form.email.data, hash_code, 0)
            msg = mail.Message(
                'Password recovery', recipients=[form.email.data])
            msg.body = flask.render_template('RecoveryPasswordEmail/body.txt',
                                       recovery_link=recovery_link)
            C4GD_web.mail.send(msg)
            flask.flash('Recovery request was sent successfully', 'info')
    return {'form': form}


# NOTE(apugachev) circular dependency
# TODO(apugacehv) get rid off functions shared with invitations
from C4GD_web.models import row_mysql_queries

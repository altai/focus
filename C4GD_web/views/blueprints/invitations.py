# coding=utf-8
import datetime
import uuid

import flask
from flask import blueprints
from flaskext import mail
from flaskext import principal
from flaskext import wtf

import C4GD_web
# TODO(apugachev) look if possible to get rid of GentleException
from C4GD_web import exceptions
# TODO(apugachev) try put all clients in one module "api_clients"
from C4GD_web import utils
from C4GD_web.models import row_mysql_queries
# TODO(apugachev) look where register_user() is used,
# try to move it here in section "utils"
from C4GD_web.views import forms


bp = blueprints.Blueprint('invitations', __name__)


def register_user(username, email, password, role):
    """
        Temporary have to register user in ODB and add a user into
        keystone db using keystoneclient
    """
    def register_in_keystone():
        """
        """
        try:
            new_keystone_user = clients.clients.keystone.users.create(
                username, password, email)

            if role != 'user':
                all_roles = clients.clients.keystone.roles.list()
                for r in all_roles:
                    if r.name == role:
                        clients.clients.keystone.roles.add_user_role(
                            new_keystone_user, r,
                            tenant=flask.current_app.config[
                                'KEYSTONE_CONF']['admin_tenant_id'])
                        break
        except Exception, e:
            raise Exception("Registration fail", e.message)
        return True

    def register_in_ODB():
        """Register user in ODB.

        API 'create_user' call to ODB, then read new user from ODB and \
        returns it.
        """
        # new user
        new_user = utils.neo4j_api_call('/users', {
            "login": "",
            "username": username,
            "email": email,
            "passwordHash": utils.create_hashed_password(password),
        }, 'POST')

        # return fresh user
        user = utils.neo4j_api_call('/users', {
            "email": email
        }, 'GET')[0]
        return user

    keystone_success = register_in_keystone()

    if keystone_success:
        user = register_in_ODB()
        return user
    else:
        return None


@bp.route('finish/<invitation_hash>/', methods=['GET', 'POST'])
def finish(invitation_hash):
    """Finish invitation process.

    Check everything, create user, redirect to logout
    (it wipes out session and redirects to login).
    """
    try:
        invitation_id, email, hash_code, complete, role = \
            row_mysql_queries.get_invitation_by_hash(invitation_hash)
    except TypeError:
        # hash code not found, None returned
        # TODO(apugachev) show form to typ e invitation token
        flask.flash('Invitation token not found.', 'error')
        return flask.redirect(flask.url_for('dashboard'))

    if complete == 1:
        flask.flash('Invitation token is already used.', 'error')
        return flask.redirect(flask.url_for('dashboard'))

    form = forms.InviteRegister()
    username = email.split("@")[0]
    form.email.data = email
    username_is_taken = False
    try:
        user = utils.neo4j_api_call('/users', {
            "email": email
        }, 'GET')[0]
        flask.flash(
            'This username is already taken. Please, choose another one.',
            'warning')
        # NOTE(apugachev) at the beginning 'username' is HiddenField
        # now we want to allow user to edit username
        # that's why bind()
        username_field = wtf.TextField(
            'Username', [wtf.Required()]).bind(form, 'username')
        form.username = username_field
        form._fields['username'] = username_field
        username_is_taken = True
    except Exception, e:
        # NOTE(apugachev) user not found, success;
        # TODO(apugachev) find out what exceptions can occur and what to do
        if form.validate_on_submit():
            new_odb_user = authentication.register_user(
                form.username.data, form.email.data, form.password.data, role)
            if new_odb_user is not None:
                row_mysql_queries.update_invitation(
                    invitation_id, email, hash_code)
                # NOTE(apugachev)no flash, it gets deleted on logout
                return flask.redirect(flask.url_for('logout'))
    form.username.data = username
    return {
        'form': form,
        'email': email,
        'username': username,
        'username_is_taken': username_is_taken
        }


@bp.route('', methods=['GET', 'POST'])
def invite():
    """Send invitation.

    Admins are allowed to invite admins and members, members - only members.
    """
    masks = row_mysql_queries.get_masks()
    form = forms.Invite()
    if form.validate_on_submit():
        user_email = form.email.data
        try:
            user = utils.neo4j_api_call('/users', {
                "email": user_email
            }, 'GET')[0]
            flask.flash(
                'User with email "%s" is already registered' % user_email,
                'error')
        except (KeyError, exceptions.GentleException):
            # NOTE(apugachev) success, user does not exist
            hash_code = str(uuid.uuid4())
            domain = user_email.split('@')[-1]
            if (domain,) not in masks:
                flask.flash('Not allowed email mask')
            else:
                row_mysql_queries.save_invitation(
                    user_email, hash_code, form.role.data)
                invite_link = "http://%s%s" % (
                    flask.request.host,
                    flask.url_for('.finish', invitation_hash=hash_code))
                msg = mail.Message('Invitation', recipients=[user_email])
                msg.body = flask.render_template(
                    'invitations/email_body.txt', invite_link=invite_link)
                C4GD_web.mail.send(msg)
                flask.flash('Invitation sent successfully', 'info')
    return {
        'form': form,
        'masks': masks
        }

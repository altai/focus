# -*- coding: utf-8 -*-

# Focus
# Copyright (C) 2010-2012 Grid Dynamics Consulting Services, Inc
# All Rights Reserved
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program. If not, see
# <http://www.gnu.org/licenses/>.

import uuid

import flask
from flask import blueprints
from flaskext import mail
from flaskext import wtf

import focus
from focus import clients
# TODO(apugachev) look if possible to get rid of GentleException
# TODO(apugachev) try put all clients in one module "api_clients"
from focus import utils
from focus.models import row_mysql_queries
# TODO(apugachev) look where register_user() is used,
# try to move it here in section "utils"
from focus.views import forms

from openstackclient_base.exceptions import NotFound


bp = blueprints.Blueprint('invitations', __name__)


def _register_in_ODB(username, email, password):
    """Register user in ODB.

    API 'create_user' call to ODB, then read new user from ODB and \
    returns it.
    """
    # new user
    utils.neo4j_api_call('/users', {
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


def register_user(username, email, password, role):
    """
        Temporary have to register user in ODB and add a user into
        keystone db using keystoneclient
    """
    def register_in_keystone():
        """
        """
        try:
            new_keystone_user = clients.admin_clients().keystone.users.create(
                username, password, email)

            if role != 'user':
                all_roles = clients.admin_clients().keystone.roles.list()
                for r in all_roles:
                    if r.name.lower() == role.lower():
                        clients.admin_clients().keystone.roles.add_user_role(
                            new_keystone_user, r,
                            tenant=clients.get_systenant_id()
                        )
                        break
                else:
                    flask.current_app.logger(
                        'Matching Keystone role for %s nto found.' % role.lower(), 
                        'error')
            return new_keystone_user
        except Exception, e:
            raise Exception("Registration fail", e.message)

    if utils.username_is_taken(email):
        raise Exception('Username is already taken')

    keystone_user = register_in_keystone()

    if keystone_user is not None:
        try:
            user = _register_in_ODB(username, email, password)
            return user
        except Exception, e:
            # revert new user creation in Keystone
            roles = keystone_user.list_roles()
            for role in roles:
                clients.admin_clients().keystone.tenants.remove_user(
                    role.tenant['id'], keystone_user, role.role['id'])
            clients.admin_clients().keystone.users.delete(keystone_user)
            raise Exception('Registration was interrupted, please try again')
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
        utils.neo4j_api_call('/users', {
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
    except Exception:
        # NOTE(apugachev) user not found, success;
        # TODO(apugachev) find out what exceptions can occur and what to do
        if form.validate_on_submit():
            new_odb_user = register_user(
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
        # Check if required conf setting exists
        _conf = flask.current_app.config
        if not 'KEYSTONE_CONF' in _conf or not 'NEO4J_API_URL' in _conf:
            raise Exception("""No required settings:
            KEYSTONE_CONF or NEO4J_API_URL, invitations wasn't sent""", "")
        user_email = form.email.data
        if not utils.username_is_taken(user_email):
            try:
                utils.neo4j_api_call('/users', {
                    "email": user_email
                }, 'GET')[0]
                flask.flash(
                    'User with email "%s" is already registered' % user_email,
                    'error')
            except (KeyError, NotFound):
                # NOTE(apugachev) success, user does not exist
                hash_code = str(uuid.uuid4())
                domain = user_email.split('@')[-1]
                if (domain,) not in masks:
                    flask.flash('Not allowed email mask')
                else:
                    row_mysql_queries.save_invitation(
                        user_email, hash_code, form.role.data)
                    invite_link = flask.url_for('.finish', invitation_hash=hash_code)
                    msg = mail.Message('Invitation', recipients=[user_email])
                    msg.body = flask.render_template(
                        'invitations/email_body.txt', invite_link=invite_link)
                    utils.send_msg(msg)
                    flask.flash('Invitation sent successfully', 'info')
    return {
        'form': form,
        'masks': masks,
        'title': bp.name.replace('_', ' ').capitalize(),
        'subtitle': 'Send invitation'
    }

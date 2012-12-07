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


import base64
import hashlib
import socket
import sys

import flask

import focus
from focus import clients

from openstackclient_base.client import HttpClient
from openstackclient_base.exceptions import NotFound


notifications_client = HttpClient()


def select_keys(d, keys, strict_order=True):
    if strict_order:
        for k in keys:
            yield d[k]
    else:
        for k, v in d.items():
            if k in keys:
                yield v


def create_hashed_password(password):
    """
    Creates unique hash based on users password
    """
    m = hashlib.md5()
    m.update(password.encode('utf-8'))
    return "{MD5}%s" % base64.standard_b64encode(m.digest())


def notifications_api_call(path, method='GET', **kwargs):
    try:
        api_url = flask.current_app.config['NOTIFICATIONS_API_URL']
    except KeyError:
        flask.current_app.logger.error(
            'Not set notifications API URL (NOTIFICATIONS_API_URL).')
        raise
    try:
        ret = notifications_client.request(
            '%s%s' % (api_url, path),
            method,
            **kwargs)[1]
    except socket.error, e:
        e.public_message = ('Can\'t connect to notifications daemon "%s".' %
                            api_url)
        flask.current_app.logger.error(e.public_message)
        raise e
    try:
        return ret["values"]
    except:
        return ret


def user_tenants_list(keystone_user):
    """
    Returns a list of tenants in which keystone_user has
    admin or member role.

    Important: Should return dicts instead of Keystone client internal objects
    because this value will be stored in session and cannot be normally
    serialized.
    """
    roles = (clients.admin_clients().identity_admin.roles.
             roles_for_user(keystone_user))
    user_tenants = {}
    for role_tenant in roles:
        if (clients.role_is_admin(role_tenant.role["name"]) or
                clients.role_is_member(role_tenant.role["name"])):
            user_tenants[role_tenant.tenant["id"]] = role_tenant.tenant
    return user_tenants.values()


# TODO: get rid of these inefficient calls
def user_tenants_with_roles_list(keystone_user):
    """
    Not implemented in Keystone API feature
    Returns a list with user's roles in it
    """
    user_roles = []
    all_tenants = clients.admin_clients().keystone.tenants.list(limit=1000000)
    for tenant in all_tenants:
        roles = keystone_user.list_roles(tenant)
        if len(roles):
            user_roles.append((tenant, roles))
    return user_roles


def get_keystone_user_by_username(username):
    """
    Not implemented in Keystone API feature
    returns a user with specific username

    Important:
    Hardcore iteration through all existing users in keystone db
    """
    users = clients.admin_clients().keystone.users.list()
    for user in users:
        if user.name == username:
            return user


def get_visible_tenants():
    """Return visible tenants.

    Exclude systenants and tenants which are not enabled.
    """
    systenant_id = clients.get_systenant_id()
    return filter(
        lambda x: x.enabled and x.id != systenant_id,
        clients.admin_clients().keystone.tenants.list())


def email_is_used(email):
    """
    Checks Keystone if user with given email is already
    registered.
    """
    try:
        clients.admin_clients().keystone.users.find(email=email)
    except NotFound:
        return False
    return True


def send_msg(msg):
    try:
        focus.mail.send(msg)
    except socket.error, e:
        e.message = 'Unable to send emails'
        flask.current_app.logger.error(e.message)
        raise e

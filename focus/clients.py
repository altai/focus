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


import flask

from openstackclient_base.base import monkey_patch
monkey_patch()

from openstackclient_base.client_set import ClientSet
from openstackclient_base.client_set import HttpClient

import focus


systenant_id = None
role_name2id = None


def get_systenant_id():
    global systenant_id
    if systenant_id is None:
        conf = flask.current_app.config['KEYSTONE_CONF'].copy()
        conf['tenant_name'] = get_systenant_name()
        client = HttpClient(**conf)
        client.authenticate()
        systenant_id = client.access['token']['tenant']['id']
    return systenant_id


def get_systenant_name():
    return flask.current_app.config['SYSTENANT_NAME']


def role_is_admin(name):
    return name.lower() == "admin"


def role_is_member(name):
    return name.lower() == "member"


def role_tenant_is_admin(role_tenant):
    return (role_is_admin(role_tenant.role["name"]) and
            role_tenant.tenant["name"] == get_systenant_name())


def get_role_id(name):
    global role_name2id
    if role_name2id is None:
        role_name2id = {}
        for role in admin_clients().keystone.roles.list():
            role_name2id[role.name.lower()] = role.id
    return role_name2id[name.lower()]


@focus.app.after_request
def save_access(response):
    try:
        access = flask.g.keystone_admin.http_client.access
        if access:
            flask.session['keystone_admin'] = {'access': access}
    except AttributeError:
        pass
    keystone_scoped = flask.session.get('keystone_scoped', {})
    for tenant_id, client in flask.g.keystone_scoped.iteritems():
        access = client.http_client.access
        if access:
            flask.session['keystone_scoped'][tenant_id] = {'access': access}
    flask.session['keystone_scoped'] = keystone_scoped
    return response


@focus.app.before_request
def get_access():
    try:
        access = flask.session['keystone_admin']['access']
    except KeyError:
        access = None
    client_set = ClientSet(access=access,
                           **flask.current_app.config['KEYSTONE_CONF'])
    flask.g.keystone_admin = client_set

    try:
        client_set = ClientSet(
            token=flask.session['keystone_unscoped']['access']['token']['id'],
            endpoint=flask.current_app.config['KEYSTONE_CONF']['auth_uri'])
    except KeyError:
        pass
    else:
        flask.g.keystone_unscoped = client_set

    flask.g.keystone_scoped = {}


def clear_cache():
    flask.g.keystone_admin.http_client.access = None
    flask.g.keystone_scoped = {}


def admin_clients():
    return flask.g.keystone_admin


def user_clients(tenant_id):
    if tenant_id is None:
        return flask.g.keystone_unscoped
    try:
        return flask.g.keystone_scoped[tenant_id]
    except KeyError:
        pass
    try:
        access = flask.session['keystone_scoped'][tenant_id]['access']
    except:
        access = None
    client_set = ClientSet(
        token=flask.session['keystone_unscoped']['access']['token']['id'],
        auth_uri=flask.current_app.config['KEYSTONE_CONF']['auth_uri'],
        tenant_id=tenant_id,
        access=access)
    flask.g.keystone_scoped[tenant_id] = client_set
    return client_set


def create_unscoped(username, password):
    http_client = HttpClient(
        username=username,
        password=password,
        auth_uri=flask.current_app.config['KEYSTONE_CONF']['auth_uri'])
    http_client.authenticate()
    flask.g.keystone_unscoped = ClientSet(http_client=http_client)
    flask.session['keystone_unscoped'] = {'access': http_client.access}
    return flask.g.keystone_unscoped

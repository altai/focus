# coding=utf-8
import base64
import hashlib
import socket
import sys

import flask

from focus import clients

from openstackclient_base.client import HttpClient
from openstackclient_base.exceptions import NotFound


neo4j_client = HttpClient()


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


def neo4j_api_call(path, params={}, method='GET'):
    try:
        api_url = flask.current_app.config['NEO4J_API_URL']
    except KeyError:
        flask.current_app.logger.error(
            'Not set ODB API URL (NEO4J_API_URL).')
        raise
    if method in ('GET', 'HEAD'):
        body = None
    else:
        body = params
        params = {}
    try:
        return neo4j_client.request(
            '%s%s' % (api_url, path),
            method,
            params=params,
            body=body)[1]
    except socket.error:
        flask.current_app.logger.error(
            'Can\'t connect to ODB "%s".' % api_url)
        raise


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


def username_is_taken(email):
    """
    Checks both Keystone and ODB if user with given email is already
    registered.
    """
    try:
        neo4j_api_call('/users', {
            "email": email
        }, 'GET')[0]
        username_is_taken = True
    except (KeyError, NotFound):
        username_is_taken = False
    else:
        try:
            user = get_keystone_user_by_username(email.split('@')[0])
            if user is None:
                username_is_taken = False
        except RuntimeError:
            username_is_taken = True
    if username_is_taken:
        flask.flash(
            'User with email "%s" is already registered' % email,
            'error')
    return username_is_taken

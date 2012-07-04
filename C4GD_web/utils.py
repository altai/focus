# coding=utf-8
import base64
import functools
import hashlib
import json
import requests
import sys

import flask

from C4GD_web import clients
from C4GD_web import exceptions


def unjson(response, attr='content'):
    if attr == 'read()':
        value = response.read()
    else:
        value = getattr(response, attr)
    if hasattr(response, 'getheaders'):
        ct = response.getheader('content-type')
    else:
        ct = response.headers['content-type']
    if 'json' in ct:
        if '' == value:
            return value
        else:
            return json.loads(value)
    else:
        return value


def response_ok(response):
    return  200 <= response.status_code < 300


def select_keys(d, keys, strict_order=True):
    if strict_order:
        for k in keys:
            yield d[k]
    else:
        for k, v in d.items():
            if k in keys:
                yield v


def get_public_url_token(tenant_id, service_type, path):
    """
    Return public url and token for Openstack service of a given type.

    Can raise exception if url can't be found.
    This function depends on an unscoped token for tenant_id in the session.
    """
    http_client = clients.user_clients(tenant_id).http_client
    if not http_client.access:
        http_client.authenticate()
    url = http_client.concat_url(
        http_client.url_for('publicURL', service_type),
        path)
    return url, http_client.access["token"]["id"],


def openstack_api_call(service_type, tenant_id, path, params={},
                       http_method=False):
    '''
    Perform call to Nova API. Manage tokens yourself.
    Return unserialized data or raise an exception.

    tenant_id - ID of tenant object. Can be string value, eg. UUID.
    path - server API path to request, eg. '/servers'
    params - data structure to serialize and pass to server
    try to get scoped token for tenant again and try one more time.

    Can raise GentleException in case any problems with API appear.
    Can raise AssertionError if http_method was not passed in (unwrapped
    function was called).
    '''
    assert http_method, 'Use wrapped Nova API calls'

    def perform(tenant_id, path, params={}):
        '''
        Calls API.

        Separate function is easy to retry.
        '''
        url, token = get_public_url_token(tenant_id, service_type, path)
        headers = {
            'X-Auth-Token': token,
            'Content-Type': 'application/json'
        }

        if http_method in [requests.post, requests.put, requests.patch]:
            kw = {'data': json.dumps(params)}
        else:
            kw = {'params': params}

        if flask.current_app.debug:
            config = {'verbose': sys.stdout}
        else:
            config = {}

        response = http_method(
            url,
            headers=headers,
            config=config,
            **kw
        )

        if flask.current_app.debug:
            flask.current_app.logger.info(headers)
            flask.current_app.logger.info(kw)
            flask.current_app.logger.info(response.content)

        return response

    response = perform(tenant_id, path, params)
    if not response_ok(response):
        try:
            r = unjson(response)
            if 'cloudServersFault' in r:
                raise exceptions.GentleException(
                    'API response was: %s' %
                    r['cloudServersFault']['message'], response)
            elif 'itemNotFound' in r:
                raise exceptions.GentleException(
                    'API response was: %s' %
                    r['itemNotFound']['message'], response)
            else:
                raise exceptions.GentleException(
                    'API response was: %s' % r, response)
        except Exception:
            raise
        else:
            raise exceptions.GentleException(
                'Can\'t make API call for %s for tenant "%s"' % (
                    service_type, tenant_id), response)
    return unjson(response)


def create_hashed_password(password):
    """
    Creates unique hash based on users password
    """
    m = hashlib.md5()
    m.update(password.encode('utf-8'))
    return "{MD5}%s" % base64.standard_b64encode(m.digest())


def neo4j_api_call(path, params={}, method='GET'):
    url = flask.current_app.config['NEO4J_API_URL'] + path
    headers = {'Content-Type': 'application/json'}

    if method == 'POST':
        response = requests.post(
            url,
            data=json.dumps(params),
            headers=headers)
    if method == 'GET':
        response = requests.get(
            url,
            params=params,
            headers=headers)
    if method == 'PUT':
        response = requests.put(
            url,
            data=json.dumps(params),
            headers=headers)
    if method == 'DELETE':
        response = requests.delete(
            url,
            data=json.dumps(params),
            headers=headers)
    if response.status_code != 404:
        if not response_ok(response):
            raise exceptions.GentleException(
                'ODB request returned %s' % response.status_code, response)
    return unjson(response)


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
    except (KeyError, exceptions.GentleException):
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

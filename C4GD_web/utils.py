# coding=utf-8
import json
import functools
import requests
import sys
import base64, hashlib

from flask import session, flash, current_app

from C4GD_web.exceptions import KeystoneExpiresException, GentleException, BillingAPIError
import functools

import sys

from flask import session, flash, current_app

from C4GD_web.exceptions import KeystoneExpiresException, GentleException, BillingAPIError
from C4GD_web.clients import clients
from C4GD_web.benchmark import benchmark

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


def keystone_obtain_unscoped(user_name, password):
    with benchmark('Getting token via REST'):
        request_data = json.dumps({
                'auth': {
                    'passwordCredentials': {
                        'username': user_name,
                        'password': password
                        },
                    }
                })
        response = requests.post(
            '%s/tokens' % current_app.config['KEYSTONE_CONF']['auth_uri'],
            data=request_data,
            headers = {'content-type': 'application/json'})
    if response_ok(response):
        return True, unjson(response)
    return False, ""
    

def keystone_get(path, params={}, is_admin=False):
    url = current_app.config['KEYSTONE_CONF']['auth_uri'] + path
    if is_admin:
        url = url.replace('5000', '35357')
    headers = {
            'X-Auth-Token': session['keystone_unscoped']['access']\
                ['token']['id'],
            'Content-Type': 'application/json'
            }

    response = requests.get(
        url, 
        params=params, 
        headers=headers)
            
    if not response_ok(response):
        if response.status_code == 401:
            raise GentleException('Access denied', response, params)
        else:
            raise KeystoneExpiresException(
                'Identity server responded with status %d' % \
                    response.status_code, response)

    return unjson(response)


def keystone_post(path, data={}, is_admin=False):
    url = current_app.config['KEYSTONE_CONF']['auth_uri'] + path
    if is_admin:
        url = url.replace('5000', '35357')
    headers = {
            'X-Auth-Token': session['keystone_unscoped']['access']\
                ['token']['id'],
            'Content-Type': 'application/json'
            }

    response = requests.post(
        url, 
        data=json.dumps(data), 
        headers=headers)
    if not response_ok(response):
        if response.status_code == 401:
            raise GentleException('Access denied', response, data)
        else:
            raise KeystoneExpiresException(
                'Identity server responded with status %d' % \
                    response.status_code, response)

    return unjson(response)

def keystone_delete(path):
    url = current_app.config['KEYSTONE_CONF']['auth_uri'] + path
    url = url.replace('5000', '35357')
    headers = {
            'X-Auth-Token': session['keystone_unscoped']['access']\
                ['token']['id'],
            'Content-Type': 'application/json'
            }

    response = requests.delete(
        url, 
        headers=headers)

    if not response_ok(response):
        if response.status_code == 401:
            raise GentleException('Access denied', response, {})
        else:
            raise KeystoneExpiresException(
                'Identity server responded with status %d' % \
                    response.status_code, response)
            

def get_public_url(tenant_id, service_type):
    """
    Return public url for Openstack service of a given type.

    Can raise exception if url can't be found.
    This function depends on scoped token for tenant_id in the session.
    """
    catalog = session['keystone_scoped'][tenant_id]['access']['serviceCatalog']
    for endpoint  in catalog:
        if endpoint['type'] == service_type:
            return endpoint['endpoints'][0]['publicURL']
    raise GentleException(
        'No public URL for %s for tenant "%s"' % (
            service_type, tenant_id))



def openstack_api_call(service_type, tenant_id, path, params={}, http_method=False):
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
        url = get_public_url(tenant_id, service_type) + path
        headers = {
            'X-Auth-Token': session['keystone_scoped'][tenant_id]['access']\
                ['token']['id'],
            'Content-Type': 'application/json'
            }

        if http_method in [requests.post, requests.put, requests.patch]:
            kw = {'data': json.dumps(params)}
        else:
            kw = {'params': params}

        if current_app.debug:
            config = {'verbose': sys.stdout}
        else:
            config = {}

        response = http_method(
            url, 
            headers=headers,
            config=config,
            **kw
            )

        if current_app.debug:
            current_app.logger.info(headers)
            current_app.logger.info(kw)
            current_app.logger.info(response.content)

        return response

    response = perform(tenant_id, path, params)
    if  not response_ok(response):
        obtain_scoped(tenant_id)
        response = perform(tenant_id, path, params)
        if  not response_ok(response):
            try:
                r = unjson(response)
                if 'cloudServersFault' in r:
                    raise GentleException(
                        'API response was: %s' % \
                            r['cloudServersFault']['message'], response)
                elif 'itemNotFound' in r:
                    raise GentleException(
                        'API response was: %s' % \
                            r['itemNotFound']['message'], response)
                else:
                    raise GentleException(
                        'API response was: %s' % r, response)
            except Exception:
                raise
            else:
                raise GentleException(
                    'Can\'t make API call for %s for tenant "%s"' % (
                        service_type, tenant_id), response)
    return unjson(response)        


def obtain_scoped(tenant_id, is_admin=True):
    data = keystone_post(
        'tokens',
        data={
            'auth': {
                'token' : {'id': session['keystone_unscoped']['access']['token']['id']},
                'tenantId': tenant_id,
                }
            }, is_admin=True)
    session['keystone_scoped'][tenant_id] = data


def billing_api_call(path, params={}, http_method=False):
    assert http_method, 'Use billing API functions wrapped'
    # TODO(apugachev) use BillingHeartClient
    # we have at least 1 scoped token, serviceCatalog exists.
    url = [x['endpoints'][0]['publicURL'] for x in session['keystone_scoped'].values()[0]['access']['serviceCatalog'] if x['type'] == 'nova-billing'][0] + path
    headers = {
            'X-Auth-Token': session['keystone_unscoped']['access']\
                ['token']['id'],
            'Content-Type': 'application/json'
            }

    if http_method in [requests.post, requests.put, requests.patch]:
        kw = {'data': json.dumps(params)}
    else:
        kw = {'params': params}
    if current_app.debug:
        config = {'verbose': sys.stdout}
    else:
        config = {}
    response = http_method(
        url,
        headers=headers,
        config=config,
        **kw)

    if current_app.debug:
        current_app.logger.info(headers)
        current_app.logger.info(kw)
        current_app.logger.info(response.content)
    
    if not response_ok(response):
        raise BillingAPIError('Billing API responds with code %s' % response.status_code, response)      
    
    return unjson(response)


billing_get = functools.partial(billing_api_call, http_method=requests.get)
billing_post = functools.partial(billing_api_call, http_method=requests.post)


def create_hashed_password(password):
    m = hashlib.md5()
    m.update(password)
    return "{MD5}%s" % base64.standard_b64encode(m.digest())
    

def neo4j_api_call(path, params={}, method='GET'):
    url = current_app.config['NEO4J_API_URL'] + path
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
            raise GentleException('ODB request returned %s' % response.status_code, response)
    return unjson(response)

def user_tenants_list(keystone_user):
    """
    Not implemented in Keystone API feature
    Returns a list of tenants keystone_user belongs to.
    
    Important: Should return dicts instead of Keystone client internal objects,
    because this value will be stored in session and cannot be normally 
    serialized. 
    """
    user_tenants = []
    all_tenants = clients.keystone.tenants.list(limit=1000000)
    for tenant in all_tenants:
        roles = keystone_user.list_roles(tenant)
        if len(roles):
            user_tenants.append({u'id': tenant.id, 
                                u'enabled': tenant.enabled, 
                                u'description': tenant.description, 
                                u'name': tenant.name})
    return user_tenants

def user_tenants_with_roles_list(keystone_user):
    """
    Not implemented in Keystone API feature
    Returns a list with user's roles in it 
    """
    user_roles = []
    all_tenants = clients.keystone.tenants.list(limit=1000000)
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
    users = clients.keystone.users.list()
    for user in users:
        if user.name == username:
            return user


def get_visible_tenants():
    """Return visible tenants.

    Exclude systenants and tenants which are not enabled.
    """
    systenant_id = current_app.config['KEYSTONE_CONF']['admin_tenant_id']
    return filter(
        lambda x: x.enabled,
        filter(
            lambda x: x.id != systenant_id,
            clients.keystone.tenants.list()))

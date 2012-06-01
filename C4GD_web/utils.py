# coding=utf-8
import json
import functools
import requests
import sys

from flask import session, flash, current_app

from C4GD_web.exceptions import KeystoneExpiresException, GentleException, BillingAPIError
import functools

import sys

from flask import session, flash, current_app

from C4GD_web.exceptions import KeystoneExpiresException, GentleException, BillingAPIError

from .benchmark import benchmark


def unjson(response, attr='content'):
    value = getattr(response, attr)
    return json.loads(value) if value != '' else ''


def response_ok(response):
    return  200 <= response.status_code < 300

from .benchmark import benchmark


def unjson(response, attr='content'):
    value = getattr(response, attr)
    if 'json' in response.headers['content-type']:
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
            '%s/tokens' % current_app.config['KEYSTONE_URL'],
            data=request_data,
            headers = {'content-type': 'application/json'})
    if response_ok(response):
        return True, unjson(response, attr='text')
    return False, ""
    

def keystone_get(path, params={}, is_admin=False):
    url = current_app.config['KEYSTONE_URL'] + path
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
    url = current_app.config['KEYSTONE_URL'] + path
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
    url = current_app.config['KEYSTONE_URL'] + path
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


def obtain_scoped(tenant_id):
    session['keystone_scoped'][tenant_id] = keystone_post(
        '/tokens',
        data={
            'auth': {
                'token' : {'id': session['keystone_unscoped']['access']['token']['id']},
                'tenantId': tenant_id,
                }
            })


def billing_api_call(path, params={}, http_method=False):
    assert http_method, 'Use billing API functions wrapped'
    url = current_app.config['BILLING_URL'] + path
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
        current_app.logger.info(response.content)
    
    if not response_ok(response):
        raise BillingAPIError('Billing API responds with code %s' % response.status_code, response)      
    
    return unjson(response)


billing_get = functools.partial(billing_api_call, http_method=requests.get)


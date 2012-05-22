# coding=utf-8
import json
import functools
import requests

from flask import session, flash, current_app

from C4GD_web.exceptions import KeystoneExpiresException, GentleException, BillingAPIError

from .benchmark import benchmark


def unjson(response, attr='content'):
    value = getattr(response, attr)
    return json.loads(value) if value != '' else ''


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
    

def keystone_get(path, params={}):
    url = current_app.config['KEYSTONE_URL'] + path
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
            raise GentleException('Access denied', response)
        else:
            raise KeystoneExpiresException(
                'Identity server responded with status %d' % \
                    response.status_code, response)

    return unjson(response)


def keystone_post(path, data={}):
    url = current_app.config['KEYSTONE_URL'] + path
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
            raise GentleException('Access denied', response)
        else:
            raise KeystoneExpiresException(
                'Identity server responded with status %d' % \
                    response.status_code, response)

    return unjson(response)


def get_public_url(tenant_id):
    """
    token obtained
    """
    nova_url = [endpoint['endpoints'][0]['publicURL'] for endpoint in session['keystone_scoped'][tenant_id]['access']['serviceCatalog'] if endpoint['type']==u'compute']
    if len(nova_url) == 0:
        raise GentleException('No public URL for nova for tenant "%s"' % tenant_id)
    return nova_url[0]


def nova_api_call(tenant_id, path, params={}, http_method=False):
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
        url = get_public_url(tenant_id) + path
        headers = {
            'X-Auth-Token': session['keystone_scoped'][tenant_id]['access']\
                ['token']['id'],
            'Content-Type': 'application/json'
            }

        if http_method in [requests.post, requests.put, requests.patch]:
            kw = {'data': json.dumps(params)}
        else:
            kw = {'params': params}

        response = http_method(
            url, 
            headers=headers,
            **kw
            )

        return response

    response = perform(tenant_id, path, params)
    if  not response_ok(response):
        obtain_scoped(tenant_id)
        response = perform(tenant_id, path, params)
        if  not response_ok(response):
            raise GentleException('Can\'t make API call for nova for tenant "%s"' % tenant_id, response)

    return unjson(response)        


nova_get = functools.partial(nova_api_call, http_method=requests.get)
nova_post = functools.partial(nova_api_call, http_method=requests.post)
nova_delete = functools.partial(nova_api_call, http_method=requests.delete)
        

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
    #import sys
    response = http_method(
        url,
        headers=headers,
        #config={'verbose': sys.stdout},
        **kw)

    if not response_ok(response):
        raise BillingAPIError('Billing API responds with code %s' % response.status_code, response)      

    return unjson(response)


billing_get = functools.partial(billing_api_call, http_method=requests.get)


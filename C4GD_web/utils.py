# coding=utf-8
from flask import session, flash
import requests
from C4GD_web import app
import json
from C4GD_web.exceptions import KeystoneExpiresException, GentleException, BillingAPIError


def select_keys(d, keys, strict_order=True):
    if strict_order:
        for k in keys:
            yield d[k]
    else:
        for k, v in d.items():
            if k in keys:
                yield v

def keystone_get(path, params={}):
    url = app.config['KEYSTONE_URL'] + path
    headers = {
            'X-Auth-Token': session['keystone_unscoped']['access']\
                ['token']['id'],
            'Content-Type': 'application/json'
            }
    response = requests.get(
        url, 
        params=params, 
        headers=headers)
            
    if 200 <= response.status_code < 300:
        return json.loads(response.content) 
    elif response.status_code == 401:
        raise GentleException('Access denied')
    else:
        raise KeystoneExpiresException('Identity server responded with status %d' % response.status_code)


def keystone_post(path, data={}):
    url = app.config['KEYSTONE_URL'] + path
    headers = {
            'X-Auth-Token': session['keystone_unscoped']['access']\
                ['token']['id'],
            'Content-Type': 'application/json'
            }
    response = requests.post(
        url, 
        data=json.dumps(data), 
        headers=headers)
    if 200 <= response.status_code < 300:
        return json.loads(response.content)
    elif response.status_code == 401:
        raise GentleException('Access denied')
    else:
        raise KeystoneExpiresException('Identity server responded with status %d' % response.status_code)

def get_public_url(tenant_id):
    """
    token obtained
    """
    nova_url = [endpoint['endpoints'][0]['publicURL'] for endpoint in session['keystone_scoped'][tenant_id]['access']['serviceCatalog'] if endpoint['type']==u'compute']
    if len(nova_url) == 0:
        raise GentleException('No public URL for nova for tenant "%s"' % tenant_id)
    return nova_url[0]

def nova_get(tenant_id, path, params={}):
    def get(tenant_id, path, params={}):
        url = get_public_url(tenant_id) + path
        headers = {
            'X-Auth-Token': session['keystone_scoped'][tenant_id]['access']\
                ['token']['id'],
            'Content-Type': 'application/json'
            }

        response = requests.get(
            url, 
            params=params, 
            headers=headers)
        return response

    response = get(tenant_id, path, params)
    if 200 <= response.status_code < 300:
        return json.loads(response.content) 
    else:
        obtain_scoped(tenant_id)
        response = get(tenant_id, path, params)
        if 200 <= response.status_code < 300:
            return json.loads(response.content) 
        else:
            raise GentleException('Can\'t make API call for nova for tenant "%s"' % tenant_id)


def obtain_scoped(tenant_id):
    session['keystone_scoped'][tenant_id] = keystone_post(
        '/tokens',
        data={
            'auth': {
                'token' : {'id': session['keystone_unscoped']['access']['token']['id']},
                'tenantId': tenant_id,
                }
            })


def billing_get(path, params={}):
    url = app.config['BILLING_URL'] + path
    headers = {
            'X-Auth-Token': session['keystone_unscoped']['access']\
                ['token']['id'],
            'Content-Type': 'application/json'
            }
    response = requests.get(
        url,
        params=json.dumps(params), 
        headers=headers)
    if 200 <= response.status_code < 300:
        return json.loads(response.content)
    else:
        raise BillingAPIError('Billing API responds with code %s' % response.status_code)

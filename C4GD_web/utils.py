import json # will fail in <2.6

import requests
import urlparse

from flask import request, url_for, g
from flaskext.wtf import Form, HiddenField, TextField, PasswordField, Required
from models import *


__all__ = ['get_next_url', 'get_login_form',# 'mapped_dict', 
           'get_vms_list_for_tenant']

def urljoin(base, *args):
    """
    >>> urljoin('http://172.30.0.1:8774/v1.1/6', 'servers', 'detail')
    http://172.30.0.1:8774/v1.1/6/servers/detail
    """
    return urlparse.urljoin(
        base if base.endswith('/') else base + "/", "/".join(args))


def get_next_url():
    """
    Defines URI to redirect to after login.
    It is provided as element "next" of request.args(GET) or request.form(POST).
    If it is not we use endpoint name from  app config DEFAULT_NEXT_TO_LOGIN_VIEW.
    
    Context: view.
    """
    if request.method == 'POST':
        d = request.form
    else:
        d = request.args
    return d.get('next', url_for(app.config['DEFAULT_NEXT_TO_LOGIN_VIEW']))

def get_login_form():
    """
    Creates login form class with correct default value of "next".
    
    Context: view
    """
    class LoginForm(Form):
        next = HiddenField(default=get_next_url())
        username = TextField('Username', [Required()])
        password = PasswordField('Password', [Required()])
    return LoginForm

        

def get_user_token_id_endpoint(user, tenant):
    """
    Returns token for the user on the tenant.
    Tries to get the token from the Keystone database.
    If non-expired  toekn exists uses it.
    Otherwise requests new token from Keystone REST API.
    """
    token_rs = Token.find_valid().find(user_id=user.id, tenant_id=tenant.id)
    if token_rs.count():
        enabled_endpoint_templates_id = g.store
        endpoint = g.store.find(
            Endpoint,
            endpoint_template_id=enabled_endpoint_templates_id,
            tenant_id=tenant.id
            ).one()
        endpoint_template = g.store.find(EndpointTemplate, id=endpoint.endpoint_template_id, enabled=True).one()
        public_url = endpoint_template.public_url
        if '%tenant_id%' in public_url:
            public_url = public_url.replace('%tenant_id%', str(tenant.id))
        return token_rs.values(Token.id).next(), public_url
    else:
        key = g.user.credentials.find(tenant_id=tenant.id).values(Credential.key).next()
        # keys can have  tenant name appended (concatenated with ':')
        if ':' in key:
            key = key.split(':')[0]
        request_data = json.dumps({
            'auth': {
                'passwordCredentials': {
                    'username': g.user.name,
                    'password': key},
                'tenantId': tenant.id}})
        response = requests.post(
            'http://172.18.41.1:5000/v2.0/tokens',
            data=request_data,
            headers = {'content-type': 'application/json'})
        assert response.status_code == 200
        response_data = json.loads(response.text)
        # probably should appear in keystone but we have it on hands now
        # we got a barrel of useful info here
        return response_data['access']['token']['id'], response_data['access']['serviceCatalog'][0]['endpoints'][0]['publicURL']
         
def get_vms_list_for_tenant(tenant):
    """
    Returns list of VM at tenant.
    Uses token for the user currently logged in.
    #? what is next - look in nova2ools source code what nova list does.
    """
    token_id, public_url = get_user_token_id_endpoint(g.user, tenant)
    endpoint = urljoin(public_url, 'servers', 'detail')
    headers = {
            'X-Auth-Project-Id': str(tenant.id),
            'X-Auth-Token': token_id}
    response = requests.get(endpoint, headers=headers)
    assert response.status_code == 200
    response_data = json.loads(response.text)
    return response_data['servers']

import requests
import json # will fail in <2.6
from storm.locals import *
from flask import g
from C4GD_web import app



class User(Storm):
    __storm_table__ = 'users'
    id = Int(primary=True)
    name = Unicode()
    password = Unicode()
    email = Unicode()
    enabled = Bool()
    tenant_id = Int()
    default_tenant = Reference(tenant_id, 'Tenant.id')
    user_roles = ReferenceSet(id, 'UserRole.user_id')
    credentials = ReferenceSet(id, 'Credential.user_id')

    def is_ldap_authenticated(self, password):
        import ldap
        connection = ldap.initialize(app.config['LDAP_URI'])
        dn = 'uid=%s,%s' % (
            ldap.dn.escape_dn_chars(username),
            app.config['LDAP_BASEDN'])
        try:
            connection.simple_bind_s(dn, password)
        except ldap.INVALID_CREDENTIALS:
            return False
        else:
            connection.unbind()
            return True


class Tenant(Storm):
    __storm_table__ = 'tenants'
    id = Int(primary=True)
    name = Unicode()
    desc = Unicode()
    enabled = Bool()
    user_roles = ReferenceSet(id, 'UserRole.tenant_id')


class Credential(Storm):
    __storm_table__ = 'credentials'
    id = Int(primary=True)
    user_id = Int()
    tenant_id = Int()
    type = Unicode()
    key = Unicode()
    secret = Unicode()


class UserRole(Storm):
    __storm_table__ = 'user_roles'
    id = Int(primary=True)
    user_id = Int()
    role_id = Int()
    tenant_id = Int()
    user = Reference(user_id, 'User.id')
    role = Reference(role_id, 'Role.id')
    tenant = Reference(tenant_id, 'Tenant.id')


class Role(Storm):
    __storm_table__ = 'roles'
    id = Int(primary=True)
    name = Unicode()
    desc = Unicode()
    service_id = Int()


class Service(Storm):
    __storm_table = 'services'
    id = Int(primary=True)
    name = Unicode()
    type = Unicode()
    desc = Unicode()


class EndpointTemplate(Storm):
    __storm_table__ = 'endpoint_templates'
    id = Int(primary=True)
    region = Unicode()
    service_id = Int()
    public_url = Unicode()
    admin_url = Unicode()
    internal_url = Unicode()
    enabled = Bool()
    is_global = Bool()


class Endpoint(Storm):
    __storm_table__ = 'endpoints'
    id = Int(primary=True)
    tenant_id = Int()
    endpoint_template_id = Int()
    endpoint_template = Reference(EndpointTemplate, 'endpoint_template_id')

class Token(Storm):
    __storm_table__ = 'token'
    id = Unicode(primary=True)
    user_id = Int()
    tenant_id = Int()
    expires = DateTime()

    __public_url = ''

    @property
    def public_url(self):
        return self.__public_url

    @public_url.setter
    def public_url(self, url):
        self.__public_url = url

    @classmethod
    def find_valid(cls):
        from datetime import datetime
        return g.store.find(cls, cls.expires > datetime.now())
    
    @classmethod
    def get_by_user_and_tenant(cls, user, tenant):
        '''
        Find tone in DB or obtains it from Nova REST API
        In the latter case as a side effect sets __public_url.
        '''
        rs = Token.find_valid().find(user_id=user.id, tenant_id=tenant.id)
        if rs.count():
            tenant_id_template_in_use = g.store.find(
                EndpointTemplate,
                EndpointTemplate.public_url.like('%tenant_id%')).count() > 0
            if tenant_id_template_in_use:
                subselect = Select(
                    EndpointTemplate.id,
                    EndpointTemplate.public_url.like('%tenant_id%'),
                    enabled=True)
                endpoint = g.store.find(
                    Endpoint,
                    Endpoint.endpoint_template_id.is_in(subselect),
                    tenant_id=tenant.id).one()
            else:
                endpoint = g.store.find(Endpoint, tenant_id=tenant.id).one() 
            token = rs.one()
            token.public_url = endpoint.endpoint_template.public_url.replace(
                '%tenant_id%', 
                str(tenant.id))
            return token
        else:
            key = user.credentials.find(tenant_id=tenant.id)\
                .values(Credential.key).next()
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
        
# class VirtualMachine(object):
#     __endpoint_part__ = 'servers'
#     def __init__(self, **kwargs):
#         for k, v in kwargs.items(): setattr(self, k, v)

#     @classmethod
#     def list(user, token):
#         endpoint_part = 'detail'        
        

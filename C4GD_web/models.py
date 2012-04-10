import requests
import json # will fail in <2.6
from storm.locals import *
from flask import g
from C4GD_web import app
from utils import select_keys


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
            ldap.dn.escape_dn_chars(self.name),
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
    endpoint_template = Reference(endpoint_template_id, "EndpointTemplate.id")

class Token(Storm):
    __storm_table__ = 'token'
    id = Unicode(primary=True)
    user_id = Int()
    tenant_id = Int()
    expires = DateTime()

    @classmethod
    def find_valid(cls):
        from datetime import datetime
        return g.store.find(cls, cls.expires > datetime.now())
    

# TODO: create base class for RESTful objects
# TODO: create a client Tenant to work with RESTful API
# TODO: make client reconnecting and regenerating tokens when required
# HINT: tenant client can work in a way similar to STORM Store
# HINT: objects returned by the client must work smoothly with models

from rest_decorators import *


class RESTModelBase(object):
    _key_name = 'id'
    
    def __init__(self, d):
        for k, v in d.items():
            setattr(self, k, v)

    def get_key(self):
        return getattr(self, self._key_name)


class VirtualMachine(RESTModelBase):
    path = '/servers'

    @classmethod 
    @get('/detail', is_plural=True)
    def list(cls, data, bypass=None, *a, **kw):
        assert bypass is not None
        return [cls(x) for x in data['servers'] if bypass(x['tenant_id'])]

    @classmethod
    @post('', two_phase=True)
    def spawn(cls, *args, **kwargs):
        d = args[0]
        image = g.pool.collections[Image][int(d['image'])]
        security_groups = select_keys(
            g.pool.collections[SecurityGroup],
            map(int, d.getlist('security_groups')))
        def response_handler(data, *a, **kw):
            #assert bypass is not None
            #return [cls(x) for x in data['server'] if bypass(x['tenant_id'])]
            pass
        return {
            'server': {
                'name': d['name'],
                'imageRef': image.links[0]['href'],
                'flavorRef': int(d['flavor']),
                'adminPass': d['password'],
                #'key_name': d['keypair'],
                #'security_groups': [{'name': x.name} for x in security_groups]
                }
             }, response_handler


class Image(RESTModelBase):
    path = '/images'
    
    @classmethod
    @get('', is_plural=True)
    def list(cls, data, *a, **kw):
        def int_id(x):
            x['id'] = int(x['id'])
            return x
        return map(cls, filter(int_id, data['images']))


class Flavor(RESTModelBase):
    path = '/flavors'
    
    @classmethod
    @get('/detail', is_plural=True)
    def list(cls, data, *a, **kw):
        return map(cls, data['flavors'])


class KeyPair(RESTModelBase):
    path = '/os-keypairs'
    _key_name = 'name'

    @classmethod
    @get('', is_plural=True)
    def list(cls, data, *a, **kw):
        return [cls(x['keypair']) for x in data['keypairs']]


class SecurityGroup(RESTModelBase):
    path = '/os-security-groups'
    
    @classmethod
    @get('', is_plural=True)
    def list(cls, data, *a, **kw):
        return map(cls, data['security_groups'])
        

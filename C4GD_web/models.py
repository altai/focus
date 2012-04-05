from storm.locals import *
from flask import g
from datetime import datetime


class User(Storm):
    __storm_table__ = 'users'
    # id, name, password, email, enabled,
    id = Int(primary=True)
    name = Unicode()
    password = Unicode()
    email = Unicode()
    enabled = Bool()
    tenant_id = Int()
    #
    default_tenant = Reference(tenant_id, 'Tenant.id')
    user_roles = ReferenceSet(id, 'UserRole.user_id')
    credentials = ReferenceSet(id, 'Credential.user_id')

class Tenant(Storm):
    __storm_table__ = 'tenants'
    # id, name, desc, enabled
    id = Int(primary=True)
    name = Unicode()
    desc = Unicode()
    enabled = Bool()
    #
    user_roles = ReferenceSet(id, 'UserRole.tenant_id')


class Credential(Storm):
    __storm_table__ = 'credentials'
    # id, user_id, tenant_id, type, key, secret
    id = Int(primary=True)
    user_id = Int()
    tenant_id = Int()
    type = Unicode()
    key = Unicode()
    secret = Unicode()
    #
    

class UserRole(Storm):
    __storm_table__ = 'user_roles'
    # id, user_id, role_id, tenant_id
    id = Int(primary=True)
    user_id = Int()
    role_id = Int()
    tenant_id = Int()
    #
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
    # id, region, service_id, public_url, admin_url, internal_url, enabled, is_global
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
    # id, tenant_id, endpoint_template_id
    id = Int(primary=True)
    tenant_id = Int()
    endpoint_template_id = Int()
    


class Token(Storm):
    __storm_table__ = 'token'
    # id, user_id, tenant_id, expires
    id = Unicode(primary=True)
    user_id = Int()
    tenant_id = Int()
    expires = DateTime()
    @classmethod
    def valid(cls):
        return g.store.find(Token, Token.expires > datetime.now())

from storm.locals import *

class User(Storm):
    __storm_table__ = 'users'
    # id, name, password, email, enabled,
    id = Int(primary=True)
    name = Unicode()
    password = Unicode()
    email = Unicode()
    enabled = Bool()
    tenant_id = Int() 
    default_tenant = Reference(tenant_id, 'Tenant.id')

class Tenant(Storm):
    __storm_table__ = 'tenants'
    # id, name, desc, enabled
    id = Int(primary=True)
    name = Unicode()
    desc = Unicode()
    enabled = Bool()

class UserRole(Storm):
    __storm_table__ = 'user_roles'
    # id, user_id, role_id, tenant_id
    id = Int(primary=True)
    user_id = Int()
    role_id = Int()
    tenant_id = Int()
    user = Reference(user_id, 'User.id')
    role = Reference(role_id, 'Role.id')
    tenant = Reference(tenant_id, 'Tenant.id')

class Token(Storm):
    __storm_table__ = 'token'
    # id, user_id, tenant_id, expires
    id = Unicode(primary=True)
    user_id = Int()
    tenant_id = Int()
    expires = DateTime()
    
class Role(Storm):
    __storm_table__ = 'roles'
    id = Int(primary=True)
    name = Unicode()
    desc = Unicode()
    service_id = Int()

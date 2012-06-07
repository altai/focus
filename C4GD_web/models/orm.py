# coding=utf-8
from storm.locals import *
from flask import g, current_app
from C4GD_web import app


__all__ = ['User', 'Tenant', 'Credential', 'UserRole', 'Role', 'Service', 
           'EndpointTemplate', 'Endpoint', 'Token', 'get_store']


class UserTenant(Storm):
    """
    Exclusively for m2m between user and tenant
    """
    __storm_table__ = 'user_roles'
    __storm_primary__ = 'user_id', 'tenant_id'
    user_id = Int()
    tenant_id = Int()


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

    def roles_in_tenant(self, tenant):
        user_roles = list(g.store.find(
            UserRole,
            user_id=self.id,
            tenant_id=tenant.id).values(UserRole.role_id))
        return g.store.find(
            Role, Role.id.is_in(user_roles)
            ).config(distinct=True).order_by(Role.name)

    def is_ldap_authenticated(self, password):
        import ldap
        connection = ldap.initialize(current_app.config['LDAP_URI'])
        dn = u'uid=%s,%s' % (
            ldap.dn.escape_dn_chars(self.name),
            current_app.config['LDAP_BASEDN'])
        try:
            connection.simple_bind_s(
                dn.encode('utf-8'),
                password.encode('utf-8'))
        except ldap.INVALID_CREDENTIALS:
            return False
        else:
            connection.unbind()
            return True

    def is_global_admin(self):
        return self.user_roles.find(tenant=None, role_id=1).count() > 0

    tenants = ReferenceSet('User.id', 'UserTenant.user_id', 'UserTenant.tenant_id', 'Tenant.id')

    def is_project_manager(self, tenant):
        return self.user_roles.find(UserRole.role_id.is_in([1, 4]), tenant=tenant).count() > 0

    def is_keystone_credentials_authenticated(self, password):
        return self.credentials.find(key=password).count() > 0

class Tenant(Storm):
    __storm_table__ = 'tenants'
    id = Int(primary=True)
    name = Unicode()
    desc = Unicode()
    enabled = Bool()
    user_roles = ReferenceSet(id, 'UserRole.tenant_id')

    def get_project_manager_list(self):
        user_ids = self.user_roles.find(UserRole.role_id.is_in([1, 4])).values(UserRole.user_id)
        return g.store.find(User, User.id.is_in(user_ids)).order_by(User.name)

    users = ReferenceSet('Tenant.id', 'UserTenant.tenant_id', 'UserTenant.user_id', 'User.id')
    
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
    __storm_table__ = 'services'
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
        from datetime import datetime, timedelta
        # respect timezones and have small handicap
        valid_until = datetime.now() + \
            timedelta(hours=current_app.config['RELATIVE_TO_API_HOURS_SHIFT']) + \
            timedelta(minutes=1)
        return g.store.find(cls, cls.expires > valid_until)
    

def get_store(SETTINGS_PREFIX):
    return Store(create_database(
        current_app.config[SETTINGS_PREFIX + '_DATABASE_URI']))


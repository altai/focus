from storm.locals import *
from flask import g
from C4GD_web import app


__all__ = ['User', 'Tenant', 'Credential', 'UserRole', 'Role', 'Service', 
           'EndpointTemplate', 'Endpoint', 'Token']


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

    def is_global_admin(self):
        return self.user_roles.find(tenant=None, role_id=1).count() > 0

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
        from datetime import datetime, timedelta
        # respect timezones and have small handicap
        valid_until = datetime.now() + \
            timedelta(hours=app.config['RELATIVE_TO_API_HOURS_SHIFT']) + \
            timedelta(minutes=1)
        return g.store.find(cls, cls.expires > valid_until)

from C4GD_web import app
from flask import g
from models import *

@app.context_processor
def debug_processor():
    return {
        'DEBUG': app.config['DEBUG'],
        'DEV': app.config['DEV']}


@app.context_processor
def frequent_data():
    if hasattr(g, 'user'):
        tenants_with_roles = []
        ids = list(g.user.user_roles.values(UserRole.tenant_id))
        tenants = g.store.find(Tenant, Or(*[Tenant.id == x for x in ids])).order_by(Tenant.name)
        for tenant in tenants:
            tenants_with_roles.append(
                (
                    tenant,
                    [x.role for x in tenant.user_roles.find(user_id=g.user.id).order_by(UserRole.role_id)]
                    ))
        return {
            'tenants_with_roles': tenants_with_roles
            }
    return {}

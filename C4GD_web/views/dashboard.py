# coding=utf-8
from flask import g

from C4GD_web import app
from C4GD_web.utils import obtain_scoped
from C4GD_web.models.abstract import VirtualMachine
from C4GD_web.models.orm import User


@app.route('/')
def dashboard():
    """
    Present short info and useful links for users depending on their roles.

    Global admins need to see all servers. We use nova call to one tenant
    which returns servers for all tenants. Useful bug.

    """
    context = {}
    if g.is_global_admin:
        # obtain scoped in advance
        obtain_scoped('6') 
        # all servers are returned on this api call
        context.update(dict(
                total_users=g.store.find(User).count(),
                total_projects=g.store.execute('select count(distinct(tenant_id)) from user_roles').get_one()[0],
                total_vms=len(VirtualMachine.list(tenant_id='6'))))
    return context

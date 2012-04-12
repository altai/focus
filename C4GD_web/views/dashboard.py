from flask import g, render_template

from C4GD_web import app
from C4GD_web.decorators import login_required
from C4GD_web.models import *

from lords import get_pool_as_global_admin


@app.route('/')
@login_required
def dashboard():
    total_users = g.store.find(User).count()
    total_projects = g.store.execute('select count(distinct(tenant_id)) from user_roles').get_one()[0]
    get_pool_as_global_admin()
    total_vms = len(g.pool(VirtualMachine.list))# TODO: find a normal way
    return render_template(
        'dashboard.haml',
        total_users=total_users, total_projects=total_projects, total_vms=total_vms)

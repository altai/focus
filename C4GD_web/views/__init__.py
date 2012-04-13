import authentication

from flask import g, render_template
from C4GD_web import app
from C4GD_web.models import *
from C4GD_web.decorators import login_required

from wrappers import ProjectWrapper, GlobalAdminWrapper

from flask import g, flash, request, redirect, url_for, \
    session, abort
from storm.exceptions import NotOneError

from C4GD_web import app

from C4GD_web.benchmark import benchmark

from forms import get_login_form, get_spawn_form
from C4GD_web.models import *
from utils import get_object_or_404, get_next_url
from C4GD_web import app
from C4GD_web.models import get_pool, Tenant, UserRole, VirtualMachine
from flask import g, flash, render_template, request, redirect, url_for, \
    session

from pagination import Pagination
from dataset import IntColumn, StrColumn, ColumnKeeper




@app.route('/')
@login_required
def dashboard():
    total_users = g.store.find(User).count()
    total_projects = g.store.execute('select count(distinct(tenant_id)) from user_roles').get_one()[0]
    return render_template(
        'dashboard.haml',
        total_users=total_users, total_projects=total_projects)


project_wrapper = ProjectWrapper()
global_wrapper = GlobalAdminWrapper()


@project_wrapper()
@app.route('/<int:tenant_id>/')
def show_tenant(*a):
    """
    List VMs for the project
    """
    vms = enumerate(
        sorted(
            g.pool(
                VirtualMachine.list,
                bypass=lambda d: int(d['tenant_id']) == g.tenant.id),
        key=lambda x: x.name), 1)
    return dict(tenant=g.tenant, vms=vms)

@project_wrapper
@app.route('/<int:tenant_id>/spawn_vm/')
def spawn_vm(*a):
    with benchmark('Getting form'):
        form = get_spawn_form()()
    if form.validate_on_submit():
        try:
            vm = g.pool(VirtualMachine.spawn, request.form)
        except RestfulException, e:
            flash(e.message, 'error')
        else:
            flash('Virtual machine spawned.', 'success')
            return redirect(url_for('show_tenant', tenant_id=g.tenant.id))
    return dict(form=form, tenant=g.tenant)

@project_wrapper
@app.route('/<int:tenant_id>/<int:vm_id>/remove_vm/')
def remove_vm():
    if request.method == 'POST':
        try:
            g.pool(VirtualMachine.remove, g.vm.id)
        except RestfulException, e:
            flash(e.message, 'error')
        else:
            flash('Virtual machine removed successfully.', 'success')
        return redirect(get_next_url())
    return {vm: g.vm}# use partial to show the same message as in modal


@app.route('/g/', defaults=dict(page=1))
@app.route('/g/<int:page>/')
@global_wrapper()
def global_list_vms(page):
    PER_PAGE = 10
    columns = ColumnKeeper({
        'id': IntColumn('id', 'ID'),
        'name': StrColumn('name', 'Name'),
        'user_id': StrColumn('user_id', 'User')
        }, ['id', 'name'])
    if 'columns' in request.args:
        columns.adjust(request.args.getlist('columns'))
    vms = g.pool(VirtualMachine.list)
    table_data = [[x(obj) for x in columns.selected] for obj in vms]
    p = Pagination(page, PER_PAGE, len(table_data))
    visible_data_base = (page - 1) * PER_PAGE
    visible_data = table_data[visible_data_base:visible_data_base + PER_PAGE]
    return dict(pagination=p, columns=columns.selected, data=visible_data, spare_columns=columns.spare)

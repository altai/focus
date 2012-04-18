import authentication

from flask import g, render_template

from C4GD_web import app
from C4GD_web.models import *

from wrappers import ProjectWrapper, GlobalAdminWrapper, DashboardWrapper

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
from dataset import IntColumn, StrColumn, ColumnKeeper, DataSet
from decorators import login_required
from exporter import Exporter


project_wrapper = ProjectWrapper()
global_wrapper = GlobalAdminWrapper()
dashboard_wrapper = DashboardWrapper()

@app.route('/')
@dashboard_wrapper()
def dashboard():
    total_users = g.store.find(User).count()
    total_projects = g.store.execute('select count(distinct(tenant_id)) from user_roles').get_one()[0]
    total_vms = len(g.pool(VirtualMachine.list))
    return render_template(
        'dashboard.haml',
        total_users=total_users,
        total_projects=total_projects,
        total_vms=total_vms)


@app.route('/<int:tenant_id>/')
@project_wrapper()
def show_tenant(tenant_id):
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


@app.route('/<int:tenant_id>/spawn_vm/', methods=['GET', 'POST'])
@project_wrapper()
def spawn_vm(tenant_id):
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


@app.route('/<int:tenant_id>/<int:vm_id>/remove_vm/', methods=['POST'])
@project_wrapper()
def remove_vm(tenant_id, vm_id):
    if request.method == 'POST':
        try:
            g.pool(VirtualMachine.remove, g.vm.id)
        except RestfulException, e:
            flash(e.message, 'error')
        else:
            flash('Virtual machine removed successfully.', 'success')
        return redirect(get_next_url())
    return {vm: g.vm}# use partial to show the same message as in modal


@app.route('/g/')
@global_wrapper()
def global_list_vms():
    PER_PAGE = 10
    page = int(request.args.get('page', 1))
    default_columns = ['id', 'name']
    #creating and adjusting columns vector, columns ordering
    columns = ColumnKeeper({
        'id': IntColumn('id', 'ID'),
        'name': StrColumn('name', 'Name'),
        'user_id': StrColumn('user_id', 'User')
        }, default_columns)
    if 'columns' in request.args:
        columns.adjust(request.args['columns'].split(','))
    if 'asc' in request.args or 'desc' in request.args:
        columns.order(request.args.getlist('asc'), request.args.getlist('desc'))
    
    vms = g.pool(VirtualMachine.list)
    dataset = DataSet(vms, columns)
    #import pdb; pdb.set_trace() #
    if 'export' in request.args:
        try:
            export = Exporter(
                request.args['export'], dataset.data, columns, 'vms')
        except KeyError:
            from werkzeug.datastructures import iter_multi_items
            d = request.args.copy()
            d.pop('export')
            return redirect(request.path + '?' + '&'.join((['%s=%s' % (k, v) for k, v in iter_multi_items(d)])))
        response = export()
    else:
        p = Pagination(page, PER_PAGE, len(dataset.data))
        visible_data_base = (page - 1) * PER_PAGE
        visible_data = dataset.data[
            visible_data_base:visible_data_base + PER_PAGE]
        response = dict(
            pagination=p,
            columns=columns,
            data=visible_data)
    return response

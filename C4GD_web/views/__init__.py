# coding=utf-8
import authentication

from datetime import date
from datetime import datetime
from functools import wraps
from flask import g, render_template, make_response, jsonify

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
from flask import g, flash, render_template, request, redirect, url_for, \
    session

from pagination import Pagination
from dataset import IntColumn, StrColumn, ColumnKeeper, DataSet
from exporter import Exporter
from C4GD_web.utils import nova_get, obtain_scoped, billing_get
from C4GD_web.exceptions import BillingAPIError, GentleException


def per_page():
    return 10


project_wrapper = ProjectWrapper()
global_wrapper = GlobalAdminWrapper()
dashboard_wrapper = DashboardWrapper()


def pm_only(view):
    @wraps(view)
    def decorated(*args, **kwargs):
        if g.user.is_project_manager(g.tenant):
            return view(*args, **kwargs)
        else:
            flash('The operation is not available to you.', 'error')
            return make_response(render_template('blank.haml'), 403)
    return decorated


@app.route('/')
@dashboard_wrapper()
def dashboard():
    context = {}
    if g.is_global_admin:
        obtain_scoped('6') # all servers are returned on this api call
        response_data = nova_get('6', '/servers/detail')
        context.update(dict(
                total_users=g.store.find(User).count(),
                total_projects=g.store.execute('select count(distinct(tenant_id)) from user_roles').get_one()[0],
                total_vms=len(response_data['servers'])))
    return context

@app.route('/<tenant_id>/')
@project_wrapper()
def show_tenant(tenant_id):
    """
    List VMs for the project
    """
    response_data = nova_get(tenant_id, '/servers/detail')
    vms_data = [x for x in response_data['servers'] if \
                    x['tenant_id'] == tenant_id]
    vms = enumerate(sorted(vms_data, key=lambda x: x['name']))
    return dict(vms=vms)
 

@app.route('/<tenant_id>/spawn_vm/', methods=['GET', 'POST'])
@project_wrapper()
def spawn_vm(tenant_id):
    pool = get_pool(g.user, tenant_id)
    with benchmark('Getting form'):
        form = get_spawn_form(pool)()
    if form.validate_on_submit():
        try:
            vm = pool(VirtualMachine.spawn, request.form, pool=pool)
        except RestfulException, e:
            flash(e.message, 'error')
        else:
            flash('Virtual machine spawned.', 'success')
            return redirect(url_for('show_tenant', tenant_id=tenant_id))
    return dict(form=form, tenant=g.tenant)


@app.route('/<tenant_id>/<int:vm_id>/remove_vm/', methods=['POST'])
@project_wrapper()
def remove_vm(tenant_id, vm_id):
    pool = get_pool(g.user, tenant_id)
    try:
        pool(VirtualMachine.remove, vm_id)
    except RestfulException, e:
        flash(e.message, 'error')
    else:
        flash('Virtual machine removed successfully.', 'success')
    return redirect(get_next_url())


@app.route('/g/billing/')
@global_wrapper()
def global_billing():
    try:
        billing_accounts = billing_get('/account')
    except BillingAPIError, e:
        raise GentleException(e.message)
    if len(billing_accounts):
        return redirect(
            url_for(
                'global_billing_details',
                tenant_id=billing_accounts[0]['name']))    
    else:
        raise GentleException('No billing accounts to show')
    

@app.route('/g/billing/<tenant_id>/')
@global_wrapper()
def global_billing_details(tenant_id):
    def get_tenant(x_id):
        try:
            try:
                tenant = g.store.get(Tenant, x_id)
            except TypeError:
                tenant = g.store.get(Tenant, int(x_id))
        except ValueError:
            tenant = None # Lyosha promised
        return tenant
    try:
        billing_accounts = billing_get('/account')
    except BillingAPIError, e:
        raise GentleException(e.message)
    else:
        tenants = [x for x in [get_tenant(x['name']) for x in billing_accounts] if x is not None]
    return generic_billing(tenant_id, tenants=tenants)


@app.route('/g/')
@global_wrapper()
def global_list_vms():
    class ProjectNameColumn(StrColumn):
        def __call__(self, x):
            tenant_id = int(x['tenant_id'])
            tenant = g.store.get(Tenant, tenant_id)
            return tenant.name
    page = int(request.args.get('page', 1))
    default_columns = ['id', 'name', 'project_name', 'tenant_id']
    #creating and adjusting columns vector, columns ordering
    columns = ColumnKeeper({
        'id': IntColumn('id', 'ID'),
        'name': StrColumn('name', 'Name'),
        'user_id': StrColumn('user_id', 'User'),
        'tenant_id': IntColumn('tenant_id', 'Project ID'),
        'project_name': ProjectNameColumn('project_name', 'Project Name')
        
        }, default_columns)
    if 'columns' in request.args:
        columns.adjust([x for x in request.args['columns'].split(',') if x])
    if 'asc' in request.args or 'desc' in request.args:
        columns.order(request.args.getlist('asc'), request.args.getlist('desc'))
    if 'groupby' in request.args:
        columns.adjust_groupby(request.args['groupby'])
    vms = response_data = nova_get('6', '/servers/detail')['servers']
    dataset = DataSet(vms, columns)
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
        p = Pagination(page, per_page(), len(dataset.data))
        visible_data_base = (page - 1) * per_page()
        visible_data = dataset.data[
            visible_data_base:visible_data_base + per_page()]
        response = dict(
            pagination=p,
            columns=columns,
            data=visible_data)
        if 'project_name' in columns.current_names:
            response['distinct_projects_names'] = sorted(
                dataset.get_distinct_values("project_name"))
    return response


@app.route('/<tenant_id>/users/')
@project_wrapper()
def list_users(tenant_id):
    """
    List users.
    TODO: pluggable view
    """
    users = g.tenant.users.find().order_by(User.name).config(distinct=True)
    page = int(request.args.get('page', 1))
    pagination = Pagination(page, per_page(), users.count())
    objects = users.config
    return {
        'pagination': pagination,
        'objects': users.config(offset=(page-1) * per_page(), limit=per_page())
        }


@app.route('/<tenant_id>/users/new/', methods=['GET', 'POST'])
@project_wrapper()
@pm_only
def new_user_to_project(tenant_id):
    """
    URGENT: control access
    """
    from forms import NewUserToProjectForm
    form = NewUserToProjectForm(g.user)
    if form.validate_on_submit():
        user = g.store.get(User, form.user.data)
        roles = g.store.find(Role, Role.id.is_in(form.roles.data))
        writable_store = get_store('RW')
        for role in roles:
            user_role = UserRole()
            user_role.user_id = user.id
            user_role.role_id = role.id
            user_role.tenant_id = g.tenant.id
            writable_store.add(user_role)
        writable_store.commit()
        flash('User added successfully', 'success')
        return redirect(url_for('list_users', tenant_id=tenant_id))
    return {'form': form}

@app.route('/<tenant_id>/users/remove/<int:user_id>/', methods=['POST'])
@project_wrapper()
@pm_only
def remove_user_from_project(tenant_id, user_id):
    writable_store = get_store('RW')
    try:
        rs = writable_store.find(
            UserRole, tenant_id=tenant_id, user_id=user_id)
    except TypeError:
        rs = writable_store.find(
            UserRole, tenant_id=int(tenant_id), user_id=user_id)
    for user_role in rs:
        writable_store.remove(user_role)
    writable_store.commit() 
    flash('User removed successfully', 'success')
    return redirect(url_for('list_users', tenant_id=tenant_id))
    

def generic_billing(tenant_id, tenants=None):
    """
    On non-AJAX request return page and iniate process of getting of dataset for default parameters. Parameters can be different in the fragment history and the js app can request dataset with other parameters, but in most cases we will guess correctly.
    On AJAX call get dataset for requested parameter and return it in correct formatting as JSON response.
    """
    from project_billing_dataset import Dataset, Params
    if request.is_xhr:
        p = Params(tenant_id, request.args)
        d = Dataset(p, user_id=g.user.id, tenant_id=tenant_id)
        tenant_name = session['keystone_scoped'][tenant_id]['access']['token']['tenant']['name']
        return jsonify({
            'caption': 'Billing for project %s' % tenant_name,
            'data': d.data
        })
    else:
        context = {
            'tenant_id': tenant_id
            }
        if tenants is not None:
            context.update({
                'tenants': tenants
                })
        return context


@app.route('/<tenant_id>/billing/')
@project_wrapper()
def project_billing(tenant_id):
    return generic_billing(tenant_id)

# coding=utf-8
from werkzeug.datastructures import iter_multi_items

from flask import g, request, session, current_app
from flask import redirect, url_for
from flask.blueprints import Blueprint

from C4GD_web.exceptions import BillingAPIError, GentleException
from C4GD_web.models.abstract import AccountBill, VirtualMachine
from C4GD_web.models.orm import Tenant

from .dataset import IntColumn, StrColumn, ColumnKeeper, DataSet
from .exporter import Exporter
from .generic_billing import generic_billing
from .pagination import Pagination, per_page

bp = Blueprint('global_views', __name__, url_prefix='/global/')


@bp.route('billing/')
def billing():
    '''
    Define tenant to show and redirect there.

    Not all tenants are accessible! Check '11' (pmo)
    '''
    billing_accounts = AccountBill.list()
    if len(billing_accounts):
        return redirect(
            url_for(
                '.billing_details',
                tenant_id=billing_accounts[0]['name']))    
    else:
        raise GentleException('No billing accounts to show')
    

@bp.route('billing/<tenant_id>/')
def billing_details(tenant_id):
    '''
    Present billing info for tenant.
    '''
    def get_tenant(x_id):
        try:
            try:
                tenant = g.store.get(Tenant, x_id)
            except TypeError:
                tenant = g.store.get(Tenant, int(x_id))
        except ValueError:
            tenant = None
        return tenant
    billing_accounts = AccountBill.list()
    tenants = [x for x in [get_tenant(x['name']) for x in billing_accounts] if x is not None]
    return generic_billing(tenant_id, tenants=tenants)


@bp.route('')
def list_vms():
    '''
    List all virtual machines in the cloud.
    '''
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
    vms = response_data = VirtualMachine.list(6)
    dataset = DataSet(vms, columns)
    if 'export' in request.args:
        try:
            export = Exporter(
                request.args['export'], dataset.data, columns, 'vms')
        except KeyError:

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

# coding=utf-8
from werkzeug.datastructures import iter_multi_items

from flask import g, request, session, current_app
from flask import redirect, url_for
from flask.blueprints import Blueprint

from C4GD_web.clients import clients
from C4GD_web.exceptions import BillingAPIError, GentleException
from C4GD_web.models.abstract import AccountBill, VirtualMachine, Flavor
from C4GD_web.models.orm import Tenant
from C4GD_web.views import pagination


from .dataset import IntColumn, StrColumn, ColumnKeeper, DataSet
from .exporter import Exporter
from .generic_billing import generic_billing
from keystoneclient import exceptions as keystoneclient_exceptions


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
    tenants_in_billing = []
    for x in AccountBill.list():
        try:
            # Billing API calls "ID" - "name"
            t = clients.keystone.tenants.get(x['name'])
        except keystoneclient_exceptions.NotFound:
            # sometimes Billing API returns non-existing tenant IDs
            # there is nothing in particular we can do about it
            pass
        else:
            tenants_in_billing.append(t)
    tenant = clients.keystone.tenants.get(tenant_id)
    return generic_billing(tenant, g.user, tenants=tenants_in_billing)


@bp.route('')
def list_vms():
    '''
    List all virtual machines in the cloud.
    '''
    tenants = dict([(x.id, x) for x in clients.keystone.tenants.list()])
    class ProjectNameColumn(StrColumn):
        def __call__(self, x):
            try:
                tenant = tenants[x.tenant_id]
            except KeyError:
                return '[deleted] %s' % x.tenant_id
            else:
                return tenant.name
    page = int(request.args.get('page', 1))
    default_columns = ['id', 'name', 'project_name', 'ram']
    #creating and adjusting columns vector, columns ordering
    columns = ColumnKeeper({
        'id': StrColumn('id', 'ID'),
        'name': StrColumn('name', 'Name'),
        'user_id': StrColumn('user_id', 'User'),
        'tenant_id': StrColumn('tenant_id', 'Project ID'),
        'project_name': ProjectNameColumn('project_name', 'Project Name'),
        'ram': IntColumn('ram', 'RAM'),
        'vcpus': IntColumn('vcpus', 'Number of CPUs')
        }, default_columns)
    if 'columns' in request.args:
        columns.adjust([x for x in request.args['columns'].split(',') if x])
    if 'asc' in request.args or 'desc' in request.args:
        columns.order(request.args.getlist('asc'), request.args.getlist('desc'))
    if 'groupby' in request.args:
        columns.adjust_groupby(request.args['groupby'])
    vms = clients.nova.servers.list(search_opts={'all_tenants': 1})
    flavors = dict([(x.id, x) for x in clients.nova.flavors.list()])
    for server in vms:
        try:
            flavor = flavors[server.flavor['id']]
        except KeyError:
            flavor = clients.nova.flavors.get(server.flavor['id'])
            flavors[server.flavor['id']] = flavor
        server.ram = flavor.ram
        server.vcpus = flavor.vcpus

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
        p = pagination.Pagination(dataset.data)
        visible_data = p.slice(dataset.data)
        response = dict(
            pagination=p,
            columns=columns,
            data=visible_data)
        if 'project_name' in columns.current_names:
            response['distinct_projects_names'] = sorted(
                dataset.get_distinct_values("project_name"))
    return response

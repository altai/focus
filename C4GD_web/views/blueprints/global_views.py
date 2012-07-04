# coding=utf-8
import urllib

from werkzeug import datastructures
from openstackclient_base.exceptions import NotFound

import flask
from flask import blueprints
from flaskext import principal

from C4GD_web import clients
from C4GD_web.views import dataset
from C4GD_web.views import environments
from C4GD_web.views import exporter
from C4GD_web.views import generic_billing
from C4GD_web.views import pagination


bp = environments.admin(blueprints.Blueprint('global_views', __name__))


@bp.before_request
def authorize():
    principal.Permission(('role', 'admin')).test()


@bp.route('billing/')
def billing():
    '''
    Define tenant to show and redirect there.

    Not all tenants are accessible! Check '11' (pmo)
    '''
    billing_accounts = clients.admin_clients().billing.account.list()
    if len(billing_accounts):
        return flask.redirect(
            flask.url_for(
                '.billing_details',
                tenant_id=billing_accounts[0]['name']))


@bp.route('billing/<tenant_id>/')
def billing_details(tenant_id):
    '''
    Present billing info for tenant.
    '''
    tenants_in_billing = []
    for x in clients.admin_clients().billing.account.list():
        try:
            # Billing API calls "ID" - "name"
            t = clients.admin_clients().keystone.tenants.get(x['name'])
        except NotFound:
            # sometimes Billing API returns non-existing tenant IDs
            # there is nothing in particular we can do about it
            pass
        else:
            tenants_in_billing.append(t)
    tenant = clients.admin_clients().keystone.tenants.get(tenant_id)
    return generic_billing.generic_billing(
        tenant, flask.g.user, tenants=tenants_in_billing)


@bp.route('')
def list_vms():
    '''
    List all virtual machines in the cloud.
    '''
    # not in visible tenants, but in all tenants
    tenants = dict(
        [(x.id, x) for x in clients.admin_clients().keystone.tenants.list()])

    class ProjectNameColumn(dataset.StrColumn):
        def __call__(self, x):
            try:
                tenant = tenants[x.tenant_id]
            except KeyError:
                return '[deleted] %s' % x.tenant_id
            else:
                return tenant.name
    default_columns = ['id', 'name', 'project_name', 'ram']
    #creating and adjusting columns vector, columns ordering
    columns = dataset.ColumnKeeper({
        'id': dataset.StrColumn('id', 'ID'),
        'name': dataset.StrColumn('name', 'Name'),
        'user_id': dataset.StrColumn('user_id', 'User'),
        'tenant_id': dataset.StrColumn('tenant_id', 'Project ID'),
        'project_name': ProjectNameColumn(
            'project_name', 'Project Name'),
        'ram': dataset.IntColumn('ram', 'RAM'),
        'vcpus': dataset.IntColumn('vcpus', 'Number of CPUs')
    }, default_columns)
    if 'columns' in flask.request.args:
        columns.adjust(
            [x for x in flask.request.args['columns'].split(',') if x])
    if 'asc' in flask.request.args or 'desc' in flask.request.args:
        columns.order(
            flask.request.args.getlist('asc'),
            flask.request.args.getlist('desc'))
    if 'groupby' in flask.request.args:
        columns.adjust_groupby(flask.request.args['groupby'])
    vms = clients.admin_clients().nova.servers.list(search_opts={
        'all_tenants': 1})
    flavors = dict(
        [(x.id, x) for x in clients.admin_clients().nova.flavors.list()])
    for server in vms:
        try:
            flavor = flavors[server.flavor['id']]
        except KeyError:
            flavor = clients.admin_clients().nova.flavors.get(server.flavor[
                'id'])
            flavors[server.flavor['id']] = flavor
        server.ram = flavor.ram
        server.vcpus = flavor.vcpus

    current_dataset = dataset.DataSet(vms, columns)
    if 'export' in flask.request.args:
        try:
            export = exporter.Exporter(
                flask.request.args['export'],
                current_dataset.data, columns, 'vms')
        except KeyError:
            d = flask.request.args.copy()
            d.pop('export')
            query = urllib.urlencode(datastructures.iter_multi_items(d))
            url = flask.request.path + '?' + query
            return flask.redirect(url)
        response = export()
    else:
        p = pagination.Pagination(current_dataset.data)
        visible_data = p.slice(current_dataset.data)
        response = dict(
            pagination=p,
            columns=columns,
            data=visible_data)
        if 'project_name' in columns.current_names:
            response['distinct_projects_names'] = sorted(
                current_dataset.get_distinct_values("project_name"))
    return response

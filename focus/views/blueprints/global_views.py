# -*- coding: utf-8 -*-

# Focus
# Copyright (C) 2010-2012 Grid Dynamics Consulting Services, Inc
# All Rights Reserved
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program. If not, see
# <http://www.gnu.org/licenses/>.


import urllib

from werkzeug import datastructures
from openstackclient_base.exceptions import NotFound

import flask
from flask import blueprints
from flaskext import principal

from focus import clients
from focus.views import dataset
from focus.views import environments
from focus.views import exporter
from focus.views import generic_billing
from focus.views import pagination


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
    return flask.redirect(
        flask.url_for(
            '.billing_details',
            tenant_id=billing_accounts[0]['name']
            if billing_accounts
            else clients.get_systenant_id()))


@bp.route('billing/<tenant_id>/')
def billing_details(tenant_id):
    '''
    Present billing info for tenant.
    '''
    tenant_list = clients.user_clients(
        clients.get_systenant_id()).identity_admin.tenants.list()
    tenant = filter(lambda x: x.id == tenant_id, tenant_list)
    if not tenant:
        flask.abort(404)
    tenant = tenant[0]
    return generic_billing.generic_billing(
        tenant, flask.g.user, tenant_list)


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
    response.update({
        'title': bp.name.replace('global_', '').replace('_', ' ').capitalize(),
        'subtitle': 'Virtual Machines List'
    })
    return response

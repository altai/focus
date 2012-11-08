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


"""Project managent.

Currently project is a Keystone tenant + C-level network bound to the tenant.
Admins are allowed to create project, list them all, delete project.

TODO(apugachev) finish process of project deletion
"""
import flask
from flask import blueprints

from focus import clients
from focus import utils
from focus.models import orm
from focus.views import environments
from focus.views import forms
from focus.views import pagination


from openstackclient_base.exceptions import HttpException


bp = environments.admin(blueprints.Blueprint('projects', __name__))

@bp.context_processor
def inject():
    return {
        'title': bp.name.replace('global_', '').replace('_', ' ').capitalize()
        }

@bp.route('')
def index():
    """List projects.

    List only enabled, sort by name.
    """

    tenants = utils.get_visible_tenants()
    ordered = sorted(tenants, key=lambda x: x.name)
    pagina = pagination.Pagination(ordered)
    delete_form = forms.DeleteForm()
    return {
        'objects': pagina.slice(ordered),
        'pagination': pagina,
        'delete_form': delete_form,
        'subtitle': 'List of projects'
    }


@bp.route('<object_id>', methods=['POST'])
def delete(object_id):
    """Deletes project.

    TODO(apugachev) remove images
    """
    try:
        tenant = clients.admin_clients().keystone.tenants.get(object_id)
    except Exception:
        flask.abort(404)

    form = forms.DeleteForm()
    if form.validate_on_submit():
        try:
            # refuse to delete project if it contains VMs
            vms = filter(
                lambda x: x.tenant_id == object_id,
                clients.admin_clients().nova.servers.list(
                    search_opts={'all_tenants': 1}))
            if vms:
                flask.flash('Project contains VM(s). Please delete VM(s) manually before deleting the project', 'error')
                return flask.redirect(flask.url_for('.index'))
            # detach network
            networks_client = clients.admin_clients().compute.networks
            networks = networks_client.list()
            for net in networks:
                if net.project_id == object_id:
                    networks_client.disassociate(net)
                    break
            # delete tenant
            tenant.delete()
            flask.flash('Project removed successfully.', 'success')
        except HttpException as ex:
            flask.flash('Cannot remote the project. %s' % ex.message, 'error')
    else:
        flask.flash('Form is not valid.', 'error')
    return flask.redirect(flask.url_for('.index'))


@bp.route('new/', methods=['GET', 'POST'])
def new():
    """Creates project.

    Bind network to the project at the same time.
    """
    form = forms.NewProject()
    admin_clients = clients.admin_clients()
    try:
        networks = admin_clients.compute.networks.list()
    except HttpException:
        networks = []
    else:
        networks = [
            (net.id, '%s (%s, %s)' % (net.label, net.cidr, net.vlan))
            for net in networks
            if net.project_id is None
        ]
    if not networks:
        flask.flash('No free networks available.', 'error')
        return flask.redirect(flask.url_for('.index'))

    form.network.choices = networks
    if form.validate_on_submit():
        if form.description.data:
            args = (form.name.data, form.description.data)
        else:
            args = (form.name.data, )
        tenant = admin_clients.keystone.tenants.create(*args)
        try:
            admin_clients.compute.networks.associate(
                form.network.data,
                tenant.id)
        except HttpException:
            tenant.delete()
            raise
        flask.flash('Project created.', 'success')
        return flask.redirect(flask.url_for('.index'))
    return {
        'form': form,
        'subtitle': 'Add new project'
    }

@bp.route('<object_id>/', methods=['GET', 'POST'])
def show(object_id):
    try:
        tenant = clients.admin_clients().keystone.tenants.get(object_id)
    except Exception:
        flask.abort(404)
    form = forms.ADProjectMembershipForm()
    if form.validate_on_submit():
        body = {'tenant': {
                'id': tenant.id,
                'groups': [x.strip() for x in form.groups.data.split(',')],
                'users': [x.strip() for x in form.users.data.split(',')]}}
        tenant.manager._create(
            '/tenants/%s/' % tenant.id, body, 'tenant')
        flask.flash('Active directory project membership updated.', 'success')
        return flask.redirect(flask.url_for('.show', object_id=tenant.id))
    else:
        form.groups.data = ', '.join(getattr(tenant, 'groups', []))
        form.users.data = ', '.join(getattr(tenant, 'users', []))
    return {'form': form, 'subtitle': tenant.name}

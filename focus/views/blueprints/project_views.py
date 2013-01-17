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


import json
import re

import flask
from flask import blueprints

from focus import clients
from focus.views import forms
from focus.views import generic_billing
from focus.views import pagination
from focus.views import utils as views_utils
from focus.views import environments
from focus.views.blueprints import images

from openstackclient_base.exceptions import NotFound

bp = environments.project(blueprints.Blueprint('project_views', __name__))


@bp.route('')
def show_tenant():
    """
    List VMs for the project
    """
    c = clients.user_clients(flask.g.tenant_id)
    servers = c.compute.servers.list(detailed=True)
    vms_data = [s._info for s in servers]
    vms_data = sorted(vms_data, key=lambda x: x['name'])
    p = pagination.Pagination(vms_data)
    data = p.slice(vms_data)
    user_id2name = {}
    uuid_regex = re.compile(
        r'[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}')
    for x in data:
        user_id = x['user_id']
        try:
            x['user_id'] = user_id2name[user_id]
            pass
        except KeyError:
            if user_id.isdigit() or uuid_regex.match(user_id):
                try:
                    user = clients.admin_clients().keystone.users.get(user_id)
                    user_id2name[user_id] = user.name
                    x['user_id'] = user.name
                except:
                    pass
    return {
        'vms': data,
        'pagination': p,
        'title': 'Virtual Machines',
        'subtitle': 'List of virtual machines'
    }


@bp.route('vms/spawn/', methods=['GET', 'POST'])
def spawn_vm():
    '''
    Spawn VM in the tenant.

    '''
    c = clients.user_clients(flask.g.tenant_id)
    images_list = images.get_images_list()
    flavors = c.compute.flavors.list()
    security_groups = c.compute.security_groups.list()
    key_pairs = c.compute.keypairs.list()

    form = forms.get_spawn_form(images_list,
                                flavors,
                                security_groups,
                                key_pairs)()

    if form.validate_on_submit():
        kw = dict(security_groups=form.security_groups.data)
        if form.keypair.data:
            kw['key_name'] = form.keypair.data
        if form.password.data:
            kw['admin_pass'] = form.password.data
        server = c.nova.servers.create(form.name.data,
                                       form.image.data,
                                       form.flavor.data,
                                       **kw)
        if server.status == 'ERROR':
            if not server.hostId:
                flask.flash('No host found to run virtual machine.', 'error')
            else:
                flask.flash('Failed to spawn virtual machine.', 'error')
        else:
            flask.flash('Virtual machine spawned.', 'success')
        return flask.redirect(flask.url_for(
            '.show_tenant', tenant_id=flask.g.tenant_id))
    return {
        'form': form,
        'tenant': flask.g.tenant,
        'images': json.dumps([x._info for x in images_list]),
        'flavors': json.dumps([x._info for x in flavors]),
        'title': 'Virtual Machines',
        'subtitle': 'Spawn new virtual machine'
    }

def check_vm_tenant(vm_id):
    server = clients.admin_clients().nova.servers.get(vm_id)
    if server.tenant_id != flask.g.tenant_id:
        flask.abort(401)
    return server

@bp.route('vms/<vm_id>/')
def show_vm(vm_id):
    server = check_vm_tenant(vm_id)
    try:
        flavor = clients.admin_clients().nova.flavors.get(server.flavor['id'])
    except NotFound:
        flavor = None
    try:
        image = clients.admin_clients().nova.images.get(server.image['id'])
    except NotFound:
        image = None
    return {
        'server': server,
        'flavor': flavor,
        'image': image,
        'title': 'Virtual Machines',
        'subtitle': 'Virtual machine details'
    }


@bp.route('vms/<vm_id>/vnc')
def get_vnc_console(vm_id):
    check_vm_tenant(vm_id)
    vnc = (clients.user_clients(flask.g.tenant_id).compute.servers.
           get_vnc_console(vm_id, flask.current_app.config['VNC_CONSOLE_TYPE']))
    return flask.redirect(vnc['console']['url'])


@bp.route('vms/<vm_id>/remove/', methods=['POST'])
def remove_vm(vm_id):
    '''
    Delete VM.
    No checks because currently OpenStack performs authorization checks.
    '''
    check_vm_tenant(vm_id)
    clients.user_clients(flask.g.tenant_id).compute.servers.delete(vm_id)
    flask.flash('Delete operation requested for VM.', 'success')
    # NOT(apugachev)openstack can be slow; make a note to reflect the fact
    # of removing the VM on the next step
    if 'removed_vms' not in flask.session:
        flask.session['removed_vms'] = []
    flask.session['removed_vms'].append(vm_id)
    return flask.redirect(views_utils.get_next_url())


@bp.route('vms/<vm_id>/reboot/<type>/', methods=['POST'])
def reboot_vm(vm_id, type):
    """
    Reboot VM
    """
    check_vm_tenant(vm_id)
    clients.user_clients(flask.g.tenant_id).compute.servers.reboot(vm_id, type)
    flask.flash('Virtual machine rebooted successfully.', 'success')
    return flask.redirect(views_utils.get_next_url())


@bp.route('vms/<vm_id>/console')
def get_console_output(vm_id):
    check_vm_tenant(vm_id)
    console = clients.user_clients(flask.g.tenant_id).compute.servers.get_console_output(vm_id)
    console = console.split('\n')
    return {
        'title': 'Console output',
        'log': console
        }


@bp.route('billing/')
def billing():
    return generic_billing.generic_billing(flask.g.tenant, flask.g.user)


@bp.route('users/')
def list_users():
    """
    List users.
    """
    users = flask.g.tenant.list_users()
    p = pagination.Pagination(users)
    return {
        'pagination': p,
        'objects': p.slice(users),
        'title': 'Users',
        'subtitle': 'List of users'
    }


@bp.route('get-credentials/')
def get_credentials():
    user = flask.session['keystone_unscoped']['access']['user']['username']
    tenant = clients.admin_clients().keystone.tenants.get(
        flask.g.tenant_id).name
    keystone_url = flask.current_app.config['KEYSTONE_CONF']['auth_uri']
    credentials_text = flask.render_template(
        'project_views/get_credentials.txt',
        **{
            'user': user,
            'tenant': tenant,
            'keystone_url': keystone_url})
    if 'download' in flask.request.args:
        response = flask.make_response(credentials_text)
        response.headers['Content-Disposition'] = \
            'attachment; filename=nova-rc-%s' % tenant
        response.headers['Content-Type'] = 'text/plain'
        return response
    else:
        return {
            'credentials_text': credentials_text,
            'title': 'Project credentials',
            'subtitle': 'Project credentials'
        }

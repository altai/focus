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

import flask
from flask import blueprints

from focus import clients

from focus.views import environments
from focus.views import forms
from focus.views import pagination

from openstackclient_base.exceptions import HttpException


bp = environments.admin(blueprints.Blueprint('networks', __name__))


@bp.route('')
def index():
    try:
        networks = clients.admin_clients().compute.networks.list()
    except HttpException as ex:
        networks = []
    tenants = clients.admin_clients().identity_admin.tenants.list()
    tenants = dict(((t.id, t.name) for t in tenants))
    p = pagination.Pagination(len(networks))
    offset = p.limit_offset()
    networks = [net._info for net in networks[offset[0]:offset[1]]]
    for net in networks:
        net["label"] = tenants.get(net["project_id"], net["label"])
    return {
        'objects': networks,
        'pagination': p,
        'delete_form': forms.DeleteForm(),
        'title': bp.name.replace('global_', '').replace('_', ' ').capitalize(),
        'subtitle': 'List of networks'
    }


@bp.route('<object_id>/')
def show(object_id):
    net = clients.admin_clients().compute.networks.get(object_id)
    return {
        'object': dict(((k, '-' if v is None else v)
                           for k, v in net._info.iteritems())),
        'title': bp.name.replace('global_', '').replace('_', ' ').capitalize(),
        'subtitle': 'Network details'
    }


@bp.route('new/', methods=['GET', 'POST'])
def new():
    """Create network.

    Insert record in db for network and create records for fixed IPs based on
    network CIDR.
    Creating fixed IPs like nova/network/manager.py:_create_fixed_ips()
    """
    form = forms.CreateNetwork()
    if form.validate_on_submit():
        label = 'net%s' % form.vlan.data
        try:
            networks = (clients.admin_clients().compute.networks.
                        create(label=label,
                               vlan_start=form.vlan.data,
                               cidr=form.cidr.data))
        except HttpException as ex:
            flask.flash(ex.message, 'error')
        else:
            flask.flash('Network %s created.' % label, 'success')
            return flask.redirect(flask.url_for('.index'))
    return {
        'form': form,
        'title': bp.name.replace('global_', '').replace('_', ' ').capitalize(),
        'subtitle': 'Add new network'
    }


@bp.route('delete/<object_id>/', methods=['POST'])
def delete(object_id):
    """Delete network and associated fixed IPs."""
    form = forms.DeleteForm()
    if form.validate_on_submit():
        try:
            clients.admin_clients().compute.networks.delete(object_id)
        except HttpException as ex:
            flask.flash(ex.message, 'error')
        else:
            flask.flash('Network deleted.', 'success')
    return flask.redirect(flask.url_for('.index'))

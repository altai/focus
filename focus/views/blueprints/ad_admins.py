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


"""Manage admins AD membership"""


import flask

from flask import blueprints

from focus import clients
from focus.views import environments
from focus.views import forms

from openstackclient_base import exceptions


bp = environments.admin(blueprints.Blueprint('ad_admins', __name__))


@bp.route('', methods=['GET', 'POST'])
def main():
    try:
        tenant = clients.admin_clients().keystone.tenants.get(clients.get_systenant_id())
    except exceptions.NotFound:
        flask.abort(404)

    form = forms.ADProjectMembershipForm(clients)

    if form.validate_on_submit():
        body = {'tenant': {
                'id': tenant.id,
                'groups': form.groups.data,
                'users': form.users.data}}

        tenant.manager._create(
            '/tenants/%s/' % tenant.id, body, 'tenant')
        flask.flash('Active directory project membership updated.', 'success')
        return flask.redirect(flask.url_for('.main'))
    else:
        form.groups.data = getattr(tenant, 'groups', [])
        form.users.data = getattr(tenant, 'users', [])
    return {
        'object': tenant,
        'form': form,
        'title': 'Admins',
        'subtitle': 'Active Directory Altai Administration Membership'
    }

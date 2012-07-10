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
from flaskext import principal
from focus import clients
from focus import utils

BARE_ENDPOINTS = [
    'project_images.progress'
]


def project(bp):
    @bp.url_value_preprocessor
    def preprocess_tenant_id(endpoint, values):
        flask.g.tenant_id = values.pop('tenant_id', None)
        # don't do anything substantial in url preprocessor

    @bp.url_defaults
    def substitute_tenant_id(endpoint, values):
        if 'tenant_id' in values or not flask.g.tenant_id:
            return
        if flask.current_app.url_map.is_endpoint_expecting(endpoint,
                                                           'tenant_id'):
            values['tenant_id'] = flask.g.tenant_id

    @bp.before_request
    def setup_tenant():
        if flask.request.endpoint not in BARE_ENDPOINTS:
            visible_ids = [x.id for x in utils.get_visible_tenants()]
            if flask.g.tenant_id not in visible_ids:
                flask.abort(404)
            principal.Permission(('role', 'member', flask.g.tenant_id)).test()
            flask.g.tenant = clients.admin_clients().keystone.tenants.get(
                flask.g.tenant_id)
    return bp


def admin(bp):
    @bp.before_request
    def authorize():
        """Check user is authorized.

        Only admins are allowed here.
        """
        principal.Permission(('role', 'admin')).test()
    return bp

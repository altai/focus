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

import focus
from focus import clients


principals = principal.Principal(focus.app)


@principal.identity_loaded.connect
def on_identity_loaded(sender, identity):
    """Add admin and project participation roles.

    If user is authenticated and user has admin role in systenant,
    he has role admin permission.
    If user is authenticated and user participates in a tenant,
    he has project member permission.
    Exclude endpoints which do not require authentication/authorization.
    """
    is_anon = identity.name == 'anon'
    loose_endpoints = flask.current_app.config['ANONYMOUS_ALLOWED']
    is_loose = flask.request.endpoint in loose_endpoints
    if is_loose or is_anon:
        return
    roles = (clients.admin_clients().identity_admin.roles.
             roles_for_user(identity.name))
    is_admin = False
    for role_tenant in roles:
        if clients.role_tenant_is_admin(role_tenant):
            is_admin = True
        if clients.role_is_member(role_tenant.role["name"]):
            identity.provides.add(
                ('role', 'member', role_tenant.tenant["id"]))

    if is_admin:
        identity.provides.add(('role', 'admin'))


if not focus.app.debug:
    @focus.app.errorhandler(principal.PermissionDenied)
    def forbidden(e):
        focus.app.logger.info(
            'Forbidden access for identity %s to %s' % (
                flask.session.get('identity.name', ''), flask.request.path))
        return '_forbidden.haml', {}


def allowed(*needs):
    return principal.Permission(*needs).can()
focus.app.jinja_env.tests['allowed'] = allowed

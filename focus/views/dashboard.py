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


from flaskext import principal

import focus
from focus import clients
from focus import utils


@focus.app.route('/')
def dashboard():
    """Present brief info and useful links.

    Global admins see numbers summary and links to administrative section.
    Members of projects see links to their respective projects.
    """
    context = {}
    if principal.Permission(('role', 'admin')).can():
        projects = utils.get_visible_tenants()
        project_ids = [x.id for x in projects]
        users = clients.admin_clients().keystone.users.list()
        servers = filter(
            lambda x: x.tenant_id in project_ids,
            clients.admin_clients().nova.servers.list(search_opts={
                'all_tenants': 1}))
        context.update(dict(
            total_users=len(users),
            total_projects=len(projects),
            total_vms=len(servers)))
    return context

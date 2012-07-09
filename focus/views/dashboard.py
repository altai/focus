# coding=utf-8
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

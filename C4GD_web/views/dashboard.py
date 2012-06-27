# coding=utf-8
from flaskext import principal

import C4GD_web
from C4GD_web import clients
from C4GD_web import utils


@C4GD_web.app.route('/')
def dashboard():
    """Present brief info and useful links.

    Global admins see numbers summary and links to administrative section.
    Members of projects see links to their respective projects.
    """
    context = {}
    if principal.Permission(('role', 'admin')).can():
        projects = utils.get_visible_tenants()
        project_ids = [x.id for x in projects]
        users = clients.clients.keystone.users.list()
        servers = filter(
            lambda x: x.tenant_id in project_ids,
            clients.clients.nova.servers.list(search_opts={'all_tenants': 1}))
        context.update(dict(
            total_users=len(users),
            total_projects=len(projects),
            total_vms=len(servers)))
    return context

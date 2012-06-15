# coding=utf-8
import flask

from flaskext import principal

from C4GD_web import app
from C4GD_web.clients import clients, get_my_clients
from C4GD_web import utils


@app.route('/')
def dashboard():
    """Present brief info and useful links.

    Global admins see numbers summary and links to administrative section.
    Members of projects see links to their respective projects.
    """
    context = {}
    if principal.Permission(('role', 'admin')).can():
        projects = utils.get_visible_tenants()
        project_ids = [x.id for x in projects]
        users = clients.keystone.users.list()
        servers = filter(
            lambda x: x.tenant_id in project_ids,
            clients.nova.servers.list(search_opts={'all_tenants': 1}))
        context.update(dict(
                total_users=len(users),
                total_projects=len(projects),
                total_vms=len(servers)))
    return context

# coding=utf-8
import flask

from flaskext import principal

from C4GD_web import app
from C4GD_web.clients import clients, get_my_clients


@app.route('/')
def dashboard():
    """
    Present short info and useful links for users depending on their roles.

    Global admins need to see all servers. We use nova call to one tenant
    which returns servers for all tenants. Useful bug.

    """
    context = {}
    if principal.Permission(('role', 'admin')).can():
        context.update(dict(
                total_users=len(clients.keystone.users.list()),
                total_projects=len(clients.keystone.tenants.list()),
                total_vms=len(clients.nova.servers.list(
                        search_opts={'all_tenants': 1}))))
    return context

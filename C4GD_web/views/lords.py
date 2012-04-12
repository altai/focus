from flask import g, flash, render_template, request, redirect, url_for, \
    session

from C4GD_web import app
from C4GD_web.models import get_pool, Tenant, UserRole, VirtualMachine

from base import BaseView


def get_pool_as_global_admin():
    if g.user.default_tenant is not None:
        t = g.user.default_tenant
    else:
        t = g.store.get(
            Tenant,
            g.user.user_roles.find(UserRole.tenant_id != None)[0].tenant_id)
    g.pool = get_pool(g.user, t)

class LordsView(BaseView):
    def dispatch_request(self, action='list_vms'):
        if action not in dir(self):
            app.logger.debug('Unknown action %s' % action)
            abort(404)
        get_pool_as_global_admin()
        result = getattr(self, action)()
        result = self.render(result)
        return result

    def list_vms(self):
        vms = g.pool(VirtualMachine.list)
        return 'list_vms.haml', {'vms': vms}

app.add_url_rule('/global/', defaults={'action': 'list_vms'}, view_func=LordsView.as_view('global_list_vms')) 

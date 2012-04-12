from flask import g, flash, request, redirect, url_for, \
    session, abort
from storm.exceptions import NotOneError

from C4GD_web import app

from C4GD_web.benchmark import benchmark

from forms import get_login_form, get_spawn_form
from C4GD_web.models import *
from utils import get_object_or_404, get_next_url

from base import BaseView
class CommonsView(BaseView):
    def dispatch_request(self, tenant_id, action='list', vm_id=0):
        if action not in dir(self):
            app.logger.debug('Unknown action %s' % action)
            abort(404)
        g.tenant = g.store.find(Tenant, id=tenant_id, enabled=True).one()
        if not g.tenant:
            app.logger.debug('Not found tenant %s' % tenant_id)
            abort(404)
        g.pool = get_pool(g.user, g.tenant)
        if vm_id:
            g.vm = g.pool(VirtualMachine.get, vm_id) 
            if int(g.vm.tenant_id) != g.tenant.id:
                app.logger.debug('VM does not belong to tenant: %s != %s' % (
                        repr(int(g.vm.tenant_id)), repr(g.tenant.id)))
                abort(404)
        result = getattr(self, action)()
        result = self.render(result)
        return result
    
    def list(self):
        vms = enumerate(
            sorted(
                g.pool(
                    VirtualMachine.list,
                    bypass=lambda d: int(d['tenant_id']) == g.tenant.id),
            key=lambda x: x.name), 1)
        return 'tenants/show.haml', dict(tenant=g.tenant, vms=vms)


    def spawn_vm(self):
        with benchmark('Getting form'):
            form = get_spawn_form()()
        if form.validate_on_submit():
            try:
                vm = g.pool(VirtualMachine.spawn, request.form)
            except RestfulException, e:
                flash(e.message, 'error')
            else:
                flash('Virtual machine spawned.', 'success')
                return redirect(url_for('show_tenant', tenant_id=g.tenant.id))
        return 'spawn_vm.haml', dict(form=form, tenant=g.tenant)

    def remove_vm(self):
        if request.method == 'POST':
            try:
                g.pool(VirtualMachine.remove, g.vm.id)
            except RestfulException, e:
                flash(e.message, 'error')
            else:
                flash('Virtual machine removed successfully.', 'success')
            return redirect(get_next_url())
        # get vm from the tenant URL
        return render_template('vm_details.html')


app.add_url_rule('/<int:tenant_id>/', view_func=CommonsView.as_view('show_tenant'))
def action_rule(action, need_vm_id=False):
    app.add_url_rule(
        '/<int:tenant_id>/%s/%s' % (
            action,
            '<int:vm_id>/' if need_vm_id else ''),
        defaults={'action': action},
        view_func=CommonsView.as_view(action))
action_rule('spawn_vm')
action_rule('remove_vm', True)



# @app.route('/tenants/<int:tenant_id>/')
# def show_tenant(tenant_id):
#     """
#     TODO: reorganize into pluggable view
#     TODO: control user has requested tenant
#     Shows list of VM available on the tenant
#     """
#     tenant = g.store.find(Tenant, id=tenant_id, enabled=True).one()
#     pool = get_pool(g.user, tenant)
#     vms = enumerate(pool(VirtualMachine.list, bypass=lambda tenant_id: int(tenant_id) == tenant.id)) 
#     return render_template('tenants/show.haml', tenant=tenant, vms=vms)





# @app.route('/tenants/<int:tenant_id>/spawn/', methods=['GET', 'POST'])
# def spawn_vm(tenant_id):
#     """
#     TODO: contorl user has this tenant
#     """
#     from rest_pool import RestfulException

#     with benchmark('Getting tenant'):
#         tenant = get_object_or_404(Tenant, tenant_id)
#     with benchmark('Getting pool'):
#         g.pool = get_pool(g.user, tenant)


# @app.route('/<int:tenant_id>/<int:vm_id>/<action>/', methods=['POST'])
# def vm(tenant_id, vm_id, action):
#     """
#     TODO: control who can watch this
#     """
#     tenant = g.store.get(Tenant, tenant_id)
#     g.pool = get_pool(g.user, tenant)
#     if action == 'remove':
#         g.pool(VirtualMachine.remove, vm_id)
#         flash('Virtual machine removed successfully.', 'success')
#         return redirect(get_next_url())
#     # get vm from the tenant URL
#     return render_template('vm_details.html')

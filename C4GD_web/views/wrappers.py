# coding=utf-8
import functools
import os.path
from C4GD_web.decorators import login_required
from C4GD_web import app
from C4GD_web.models import *
from flask import render_template, abort, g


class BaseWrapper(object):
    template_dir = ''
    extension = '.haml'

    def __init__(self, template_dir=None):
        if template_dir is not None:
            self.template_dir = template_dir
        else:
            self.template_dir = self.__class__.__name__.replace('Wrapper', '')


    def __call__(self, func_name=None, extension=None):
        """
        TODO: make it work as @wrapper instead of @wrapper()
        """
        def _decorator(func):
            @login_required
            @functools.wraps(func)
            def _wrapped(*args, **kwargs):
                self.before(*args, **kwargs)
                
                result = func(*args, **kwargs)
                t = type(result) 
                if t is dict:
                    result = render_template(
                        os.path.join(
                            self.template_dir, 
                            '%s%s' % (
                                func_name or func.func_name,
                                extension or self.extension)),
                        **result)
                elif t in [tuple, list] and len(result) == 2:
                    result = render_template(result[0], **result[1])
                else:
                    pass

                return result
            return _wrapped
        return _decorator

    def before(self, *args, **kwargs):
        raise NotImplementedError


class GlobalAdminWrapper(BaseWrapper):
    def before(self, *args, **kwargs):
        if g.user.default_tenant is not None:
            t = g.user.default_tenant
        else:
            t = g.store.get(
                Tenant,
                g.user.user_roles.find(UserRole.tenant_id != None)[0].tenant_id)
        g.pool = get_pool(g.user, t)


DashboardWrapper = GlobalAdminWrapper
    

class ProjectWrapper(BaseWrapper):
    def before(self, *args, **kwargs):
        g.tenant = g.store.find(Tenant, id=kwargs['tenant_id'], enabled=True).one()
        if not g.tenant:
            app.logger.debug('Not found tenant %s' % kwargs['tenant_id'])
            abort(404)
        g.pool = get_pool(g.user, g.tenant)
        vm_id = kwargs.get('vm_id', None)
        if vm_id:
            g.vm = g.pool(VirtualMachine.get, vm_id) 
            if int(g.vm.tenant_id) != g.tenant.id:
                app.logger.debug('VM does not belong to tenant: %s != %s' % (
                        repr(int(g.vm.tenant_id)), repr(g.tenant.id)))
                abort(404)



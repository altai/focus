# coding=utf-8
import functools
import os.path
from C4GD_web.decorators import login_required
from C4GD_web import app
from C4GD_web.models import *
from flask import render_template, abort, g, redirect, url_for, session, flash
from C4GD_web.exceptions import KeystoneExpiresException, GentleException
from C4GD_web.utils import obtain_scoped


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
                try:
                    before_result = self.before(*args, **kwargs)
                    result = func(*args, **kwargs)
                    t = type(result) 
                    if t is dict:
                        context = result
                        if type(before_result) is dict:
                            context.update(before_result)
                        result = render_template(
                            os.path.join(
                                self.template_dir, 
                                '%s%s' % (
                                    func_name or func.func_name,
                                    extension or self.extension)),
                            **context)
                    elif t in [tuple, list] and len(result) == 2:
                        context = result[1]
                        if type(before_result) is dict:
                            context.update(before_result)
                        result = render_template(result[0], **context)
                    else:
                        pass

                    return result
                except KeystoneExpiresException, e:
                    flash(e.message, 'error')
                    return redirect(url_for('logout'))
                except GentleException, e:
                    flash(e.message, 'error')
                    return render_template('blank.haml')
            return _wrapped
        return _decorator

    def before(self, *args, **kwargs):
        try:
            g.user = g.store.get(User, session['keystone_unscoped']['access']['user']['id'])
        except TypeError:
            g.user = g.store.get(User, int(session['keystone_unscoped']['access']['user']['id']))


class GlobalAdminWrapper(BaseWrapper):
    def before(self, *args, **kwargs):
        super(GlobalAdminWrapper, self).before(*args, **kwargs)


class DashboardWrapper(BaseWrapper):
    def before(self, *args, **kwargs):
        super(DashboardWrapper, self).before(*args, **kwargs)
    

class ProjectWrapper(BaseWrapper):
    def before(self, *args, **kwargs):
        super(ProjectWrapper, self).before(*args, **kwargs)
        tenant_id = kwargs['tenant_id']
        try:
            tenant_dict = session['keystone_scoped'][tenant_id]['access']['token']['tenant']
        except KeyError:
            obtain_scoped(tenant_id)
        try:
            tenant_dict = session['keystone_scoped'][tenant_id]['access']['token']['tenant']
        except KeyError:
            raise GentleException('Tenant %s is not accessible for you.' % tenant_id)
        tenant = g.store.get(Tenant, int(tenant_id))
        g.tenant = tenant
        user_ids = tenant.user_roles.find(UserRole.role_id.is_in([1, 4])).values(UserRole.user_id)
        project_managers = list(g.store.find(User, User.id.is_in(user_ids)).order_by(User.name).values(User.name))
            
        return dict(
            tenant=tenant_dict, 
            project_managers=project_managers)

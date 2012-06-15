# coding=utf-8
import sys
import urllib
import urlparse

from flask import g, session, request
from C4GD_web import app
from C4GD_web import clients
from C4GD_web import utils

@app.context_processor
def navigation_bar_tenant_data():
    try:
        if getattr(g, 'is_authenticated', False):
            tenants_with_roles = []
            # keystone user id
            user_id = session['keystone_unscoped']['access']['user']['id']
            # TODO(apugachev) use simpler way when keystone works correctly
            # now use simple iteration through all tenants and users
            #  user = clients.clients.keystone.users.get(user_id)
            #  roles = user.list_roles()
            
            # dont' count systenant as a project, do not list it
            tenants = utils.get_visible_tenants()
            for tenant in tenants:
                users = tenant.list_users()
                if filter(lambda x: x.id == user_id, users):
                    # TODO(apugachev) take roles from keystone API 
                    # when list_roles() works instead of obtain_scoped
                    if tenant.id not in session['keystone_scoped']:
                        utils.obtain_scoped(tenant.id)
                    # NOTE(apugachev) templates expect dicts
                    tenants_with_roles.append(
                        (tenant._info, session['keystone_scoped'][tenant.id]\
                             ['access']['user']['roles']))
            return {'tenants_with_roles': tenants_with_roles}

    except Exception:
        exc_type, exc_value, tb = sys.exc_info()
        app.log_exception((exc_type, exc_value, tb))
    return {}


def url_for_other_page(page):
    try:
        args = request.args.copy()
        args['page'] = page
        result = '%s?%s' % (
            request.path,
            urllib.urlencode(
                tuple(args.iterlists()), 
                doseq=1))
        return result

    except Exception:
        exc_type, exc_value, tb = sys.exc_info()
        app.log_exception((exc_type, exc_value, tb))
    return {}


app.jinja_env.globals['url_for_other_page'] = url_for_other_page

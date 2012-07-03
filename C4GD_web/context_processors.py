# coding=utf-8
# NOTE(apugachev) all context processors return empty dictionaries on error
# and log exceptions because we want template blank.html to render always.
import sys
import urllib

import flask

import C4GD_web
from C4GD_web import utils
from C4GD_web import clients


@C4GD_web.app.context_processor
def navigation_bar_tenant_data():
    if not getattr(flask.g, 'is_authenticated', False):
        return {}
    try:
        user_id = flask.session['keystone_unscoped'][
            'access']['user']['id']
        roles = (clients.admin_clients().identity_admin.roles.
                 roles_for_user(user_id))
        roles_by_tenant = {}
        tenants = {}
        for r_t in roles:
            roles_by_tenant.setdefault(
                r_t.tenant["id"], []).append(r_t.role)
            tenants[r_t.tenant["id"]] = r_t.tenant
        tenants_with_roles = [
            (tenant, roles_by_tenant[tenant["id"]])
            for tenant in tenants.values()
            if tenant["name"] != clients.get_systenant_name()]
        return {'tenants_with_roles': tenants_with_roles}
    except Exception:
        exc_type, exc_value, tb = sys.exc_info()
        C4GD_web.app.log_exception((exc_type, exc_value, tb))
    return {}


# TODO(apugachev) gather templates-related staff like filters to separate
# module
def url_for_other_page(page):
    try:
        args = flask.request.args.copy()
        args['page'] = page
        result = '%s?%s' % (
            flask.request.path,
            urllib.urlencode(
                tuple(args.iterlists()),
                doseq=1))
        return result

    except Exception:
        exc_type, exc_value, tb = sys.exc_info()
        C4GD_web.app.log_exception((exc_type, exc_value, tb))
    return {}


C4GD_web.app.jinja_env.globals['url_for_other_page'] = url_for_other_page

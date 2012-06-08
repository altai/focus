# coding=utf-8
import sys
import urllib
import urlparse

from flask import g, session, request
from C4GD_web import app


@app.context_processor
def navigation_bar_tenant_data():
    try:
        if getattr(g, 'is_authenticated', False):
            tenants_with_roles = []
            for tenant in session['tenants']['tenants']:
                tenants_with_roles.append(
                    (tenant, session['keystone_scoped'][tenant['id']]['access']['user']['roles']))
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

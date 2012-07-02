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
    try:
        if getattr(flask.g, 'is_authenticated', False):
            tenants_with_roles = []
            # keystone user id
            user_id = flask.session[
                'keystone_unscoped']['access']['user']['id']
            # NOTE(apugachev) use simpler way when keystone works correctly
            # now use simple iteration through all tenants and users
            tenants = clients.user_clients(None).identity_public.tenants.list()
            scoped = flask.session.get('keystone_scoped', {}).keys()
            for tenant in tenants:
                # TODO(apugachev) take roles from keystone API
                # when list_roles() works instead of obtain_scoped
                if tenant.id not in scoped:
                    utils.obtain_scoped(tenant.id)
                # NOTE(apugachev) templates expect dicts
                tenants_with_roles.append(
                    (tenant._info,
                     flask.session[
                         'keystone_scoped'][tenant.id]['access'][
                             'user']['roles']))

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

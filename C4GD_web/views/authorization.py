import flask

from flaskext import principal

import C4GD_web
from C4GD_web import clients


principals = principal.Principal(C4GD_web.app)


@principal.identity_loaded.connect
def on_identity_loaded(sender, identity):
    """Add admin and project participation roles.

    If user is authenticated and user has role Admin in default admin tenant he
    has role admin permission. If user is authenticated and user participates
    in a tenant he has project member permission.
    Exclude endpoints which do not require authentication/authorization.
    """
    is_anon = identity.name == 'anon'
    loose_endpoints = flask.current_app.config['ANONYMOUS_ALLOWED']
    is_loose = flask.request.endpoint in loose_endpoints
    if not (is_loose or is_anon):
        user = clients.clients.keystone.users.get(identity.name)
        roles = clients.clients.keystone.roles.roles_for_user(
            identity.name,
            flask.current_app.config[
                'KEYSTONE_CONF']['admin_tenant_id'])
        if any([x.name == flask.current_app.config['ADMIN_ROLE_NAME'] \
                    for x in roles]):
            identity.provides.add(('role', 'admin'))
        # TODO(apugachev): use list_roles() when server implemented it
        for tenant in clients.clients.keystone.tenants.list():
            if len(user.list_roles(tenant)):
                identity.provides.add(('role', 'member', tenant.id))


if not C4GD_web.app.debug:
    @C4GD_web.app.errorhandler(principal.PermissionDenied)
    def forbidden(e):
        C4GD_web.app.logger.info(
            'Forbidden access for identity %s to %s' % (
                flask.session.get('identity.name', ''), flask.request.path))
        return '_forbidden.haml', {}


def allowed(*needs):
    return principal.Permission(*needs).can()
C4GD_web.app.jinja_env.tests['allowed'] = allowed

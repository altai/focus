import flask

from flaskext import principal

import C4GD_web
from C4GD_web import clients


principals = principal.Principal(C4GD_web.app)


@principal.identity_loaded.connect
def on_identity_loaded(sender, identity):
    """Add admin and project participation roles.

    If user is authenticated and user has admin role in systenant,
    he has role admin permission.
    If user is authenticated and user participates in a tenant,
    he has project member permission.
    Exclude endpoints which do not require authentication/authorization.
    """
    is_anon = identity.name == 'anon'
    loose_endpoints = flask.current_app.config['ANONYMOUS_ALLOWED']
    is_loose = flask.request.endpoint in loose_endpoints
    if is_loose or is_anon:
        return
    roles = (clients.admin_clients().identity_admin.roles.
             roles_for_user(identity.name))
    is_admin = False
    for role_tenant in roles:
        if clients.role_tenant_is_admin(role_tenant):
            is_admin = True
        if clients.role_is_member(role_tenant.role["name"]):
            identity.provides.add(
                ('role', 'member', role_tenant.tenant["id"]))

    if is_admin:
        identity.provides.add(('role', 'admin'))


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

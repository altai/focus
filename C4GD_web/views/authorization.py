import flask

from flaskext import principal

from C4GD_web import app
from C4GD_web.clients import clients, get_my_clients


principals = principal.Principal(app)


@principal.identity_loaded.connect
def on_identity_loaded(sender, identity):
    """Add admin and project participation roles.

    If user is authenticated and user has role Admin in default admin tenant he
    has role admin permission. If user is authenticated and user participates
    in a tenant he has project member permission.
    Exclude endpoints which do not require authentication/authorization.
    """
    is_anon = identity.name == 'anon'
    is_loose = flask.request.endpoint in flask.current_app.\
        config['ANONYMOUS_ALLOWED']
    if not (is_loose or is_anon):
        user = clients.keystone.users.get(identity.name)
        roles = clients.keystone.roles.roles_for_user(
                    identity.name, 
                    flask.current_app.config\
                        ['KEYSTONE_CONF']['admin_tenant_id'])
        if any([x.name == flask.current_app.config['ADMIN_ROLE_NAME'] \
                    for x in roles]):
            identity.provides.add(('role', 'admin'))
        # TODO(apugachev): use list_roles() when server implemented it
        for tenant in clients.keystone.tenants.list():
            if len(user.list_roles(tenant)):
                identity.provides.add(('role', 'member', tenant.id)) 


if not app.debug:
    @app.errorhandler(principal.PermissionDenied)
    def forbidden(e):
        app.logger.info(
            'Forbidden access for identity %s to %s' % (
                flask.session.get('identity.name', ''), flask.request.path))
        return '_forbidden.haml', {}


def allowed(*needs):
    return principal.Permission(*needs).can()
app.jinja_env.tests['allowed'] = allowed

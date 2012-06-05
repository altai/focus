import flask

from flaskext import principal

from C4GD_web import app
from C4GD_web.clients import clients


principals = principal.Principal(app)


@principal.identity_loaded.connect
def on_identity_loaded(sender, identity):
    '''
    Add admin and project participation roles.

    If user is authenticated and user has role Admin in default admin tenant he has role admin permission.
    If user is authenticated and user participates in a tenant he has project member permission.
    Exclude static endpoint from this.
    '''
    if flask.request.endpoint != 'static' and identity.name != 'anon':
        user = clients.keystone.users.get(identity.name)
        if any([x.name == 'Admin' \
                    for x in clients.keystone.roles.roles_for_user(
                    identity.name, 
                    flask.current_app.config['KEYSTONE_CONF']['admin_tenant_id'])]):
            identity.provides.add(('role', 'admin'))
        # TODO(apugachev): use list_roles() when server implemented it
        # TODO(apugachev): console shows ever increasing number of requests to the same URLs.
        # It needs careful investigation.
        for tenant in clients.keystone.tenants.list(limit=1000000):
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

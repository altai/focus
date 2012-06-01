import flask

from flaskext import principal

from C4GD_web import app


principals = principal.Principal(app)

@principal.identity_loaded.connect
def on_identity_loaded(sender, identity):
    '''
    Add admin and project participation roles.
    '''
    if identity.name != 'anon':
        if 'keystone_unscoped' in flask.session:
            if any([x.get('name') == 'Admin' for x in \
                        flask.session['keystone_unscoped']['access']\
                        ['user']['roles']]):
                identity.provides.add(('role', 'admin'))
        for tenant_id in flask.session.get('keystone_scoped', []):
            identity.provides.add(('project', tenant_id))

if not app.debug:
    @app.errorhandler(principal.PermissionDenied)
    def forbidden(e):
        app.logger.info(
            'Forbidden access for identity %s to %s' % (
                flask.session.get('identity.name', ''), flask.request.path))
        return '_forbidden.haml', {}

import flask
from flaskext import principal
from C4GD_web import clients
from C4GD_web import utils


def project(bp):
    @bp.url_value_preprocessor
    def preprocess_tenant_id(endpoint, values):
        flask.g.tenant_id = values.pop('tenant_id', None)
        # don't do anything substantial in url preprocessor

    @bp.url_defaults
    def substitute_tenant_id(endpoint, values):
        if 'tenant_id' in values or not flask.g.tenant_id:
            return
        if flask.current_app.url_map.is_endpoint_expecting(endpoint,
                                                           'tenant_id'):
            values['tenant_id'] = flask.g.tenant_id

    @bp.before_request
    def setup_tenant():
        visible_ids = [x.id for x in utils.get_visible_tenants()]
        if flask.g.tenant_id not in visible_ids:
            flask.abort(404)
        principal.Permission(('role', 'member', flask.g.tenant_id)).test()
        flask.g.tenant_dict = flask.session[
            'keystone_scoped'][flask.g.tenant_id]['access']['token']['tenant']
        flask.g.tenant = clients.admin_clients().keystone.tenants.get(
            flask.g.tenant_id)
        # TODO(apugachev) check with DM if it is needed to have projectmanager
#        flask.g.project_managers = [
#            user for user in flask.g.tenant.list_users() if any(
#                filter(
#                    lambda role: role.name == 'projectmanager',
#                    user.list_roles(flask.g.tenant_id)))]
    return bp


def admin(bp):
    @bp.before_request
    def authorize():
        """Check user is authorized.

        Only admins are allowed here.
        """
        principal.Permission(('role', 'admin')).test()
    return bp

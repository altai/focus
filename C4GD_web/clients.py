import flask

from openstackclient_base.base import monkey_patch
monkey_patch()

from openstackclient_base.client_set import ClientSet

import C4GD_web


@C4GD_web.app.after_request
def save_access(response):
    try:
        access = flask.g.keystone_admin.http_client.access
        if access:
            flask.session['keystone_admin'] = {'access': access}
    except AttributeError:
        pass
    keystone_scoped = flask.session.get('keystone_scoped', {})
    for tenant_id, client in flask.g.keystone_scoped.iteritems():
        access = client.http_client.access
        if access:
            flask.session['keystone_scoped'][tenant_id] = {'access': access}
    flask.session['keystone_scoped'] = keystone_scoped
    return response


@C4GD_web.app.before_request
def get_access():
    try:
        access = flask.session['keystone_admin']['access']
    except KeyError:
        access = None
    client_set = ClientSet(access=access,
                           **flask.current_app.config["KEYSTONE_CONF"])
    flask.g.keystone_admin = client_set

    try:
        client_set = ClientSet(
            token=flask.session['keystone_unscoped']['access']['token']['id'],
            endpoint=flask.current_app.config['KEYSTONE_CONF']['auth_uri'])
    except KeyError:
        pass
    else:
        flask.g.keystone_unscoped = client_set

    flask.g.keystone_scoped = {}


def admin_clients():
    return flask.g.keystone_admin


def user_clients(tenant_id):
    if tenant_id is None:
        return flask.g.keystone_unscoped
    try:
        return flask.g.keystone_scoped[tenant_id]
    except KeyError:
        pass
    try:
        access = flask.session['keystone_scoped'][tenant_id]['access']
    except:
        access = None
    client_set = ClientSet(
        token=flask.session['keystone_unscoped']['access']['token']['id'],
        auth_uri=flask.current_app.config['KEYSTONE_CONF']['auth_uri'],
        tenant_id=tenant_id,
        access=access)
    flask.g.keystone_scoped[tenant_id] = client_set
    return client_set

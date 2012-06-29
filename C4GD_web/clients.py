import flask

from openstackclient_base.base import monkey_patch
monkey_patch()

from openstackclient_base.client_set import ClientSet
from openstackclient_base.client import HttpClient


admin_client_set = None


def admin_clients():
    global admin_client_set
    if admin_client_set:
        try:
            flask.session["admin_token"] = (admin_client_set.client.
                                            access["token"]["id"])
            return admin_client_set
        except:
            pass

    conf = flask.current_app.config["KEYSTONE_CONF"].copy()
    try:
        conf["token"] = flask.session["admin_token"]
    except KeyError:
        pass
    admin_client_set = ClientSet(**conf)
    return admin_client_set


def get_my_clients(tenant_id):
    try:
        if tenant_id is None:
            admin_client = admin_clients().client
            if not admin_client.access:
                admin_client.authenticate()
            access = flask.session['keystone_unscoped']['access'].copy()
            access["serviceCatalog"] = admin_client.access["serviceCatalog"]
        else:
            access = flask.session['keystone_scoped'][tenant_id]['access']    
    except:
        conf = {
            'token': flask.session['keystone_unscoped']['access']['token']['id'],
            'auth_uri': flask.current_app.config['KEYSTONE_CONF']['auth_uri'],
            'tenant_id': tenant_id,
        }
        client = HttpClient(**conf)
        client.authenticate()
        flask.session.setdefault("keystone_scoped", {})[tenant_id] = {
            "access": client.access
        }
    else:
        client = HttpClient(token="invalid",
                            auth_uri=flask.current_app.config
                            ["KEYSTONE_CONF"]["auth_uri"])
        client.access = access
    return ClientSet(client=client)

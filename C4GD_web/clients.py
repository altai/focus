import flask
from  C4GD_web import nova_billing_heart_client


class ClientsSingleton(object):
    _clients = {}
    conf = None

    def configure(self):
        if self.conf:
            return
        self.conf = flask.current_app.config["KEYSTONE_CONF"].copy()
        endpoint = self.conf["auth_uri"]
        if endpoint.endswith("/"):
            endpoint = endpoint[:-1]
        if endpoint.endswith("/v2.0"):
            endpoint = endpoint[:-5]
        self.conf["auth_uri"] = endpoint

    def __getattr__(self, name):
        if name.startswith("_client_"):
            raise AttributeError(name)
        try:
            return self._clients[name]
        except KeyError:
            self.configure()
            ctor = getattr(self, "_client_%s" % name)
            c = ctor()
            self._clients[name] = c
            return c

    def _client_heart(self):
        return nova_billing_heart_client.BillingHeartClient(
            management_url=self.conf["billing_heart_url"])

    def _client_nova(self):
        from novaclient.v1_1.client import Client
        return Client(
            self.conf["admin_user"],
            self.conf["admin_password"],
            self.conf["admin_tenant_name"],
            "%s/v2.0" % self.conf["auth_uri"])

    def _client_keystone(self):
        from keystoneclient.v2_0.client import Client
        return Client(
            username=self.conf["admin_user"],
            password=self.conf["admin_password"],
            tenant_name=self.conf["admin_tenant_name"],
            auth_url="%s/v2.0" % self.conf["auth_uri"])

    def _client_glance(self):
        from glanceclient.v1.client import Client
        keystone = self.keystone
        endpoint = keystone.service_catalog.url_for(
            service_type="image")
        if endpoint.endswith("/"):
            endpoint = endpoint[:-1]
        if endpoint.endswith("/v1"):
            endpoint = endpoint[:-3]
        return Client(endpoint=endpoint, token=keystone.auth_token)


clients = ClientsSingleton()


class ClientSet(object):

    @staticmethod
    def strip_version(endpoint):
        if not endpoint:
            return ""
        if endpoint.endswith("/"):
            endpoint = endpoint[:-1]
        if endpoint.endswith("/v2.0"):
            endpoint = endpoint[:-5]
        if endpoint.endswith("/v1"):
            endpoint = endpoint[:-3]
        return endpoint

    def __init__(self, **conf):
        """
        Acceptable arguments:
        - auth_uri or auth_url;
        - username, password;
        - tenant_id, tenant_name=None;
        - token, region_name.
        """
        self.conf = conf.copy()
        self.conf["auth_uri"] = "%s/v2.0" % self.strip_version(
            conf.get("auth_uri") or conf.get("auth_url"))

    @property
    def keystone(self):
        conf = self.conf
        from keystoneclient.v2_0.client import Client as KeystoneClient
        keystone = KeystoneClient(
            username=conf.get("username"),
            password=conf.get("password"),
            tenant_id=conf.get("tenant_id"),
            tenant_name=conf.get("tenant_name"),
            auth_url=conf.get("auth_uri"),
            region_name=conf.get("region_name"),
            token=conf.get("token"))
        # the __init__ calls authenticate() immediately
        return keystone

    @property
    def keystone_service(self):
        keystone = self.keystone
        from keystoneclient.v2_0.client import Client as KeystoneClient
        keystone_service = KeystoneClient(
            endpoint=keystone.service_catalog.url_for(
                service_type="identity", endpoint_type="publicURL"),
            token=keystone.auth_token)
        return keystone_service

    @property
    def nova(self):
        conf = self.conf
        keystone = self.keystone
        from novaclient.v1_1.client import Client as NovaClient
        nova = NovaClient(
            conf.get("username"),
            conf.get("password"),
            conf.get("tenant_name"),
            conf.get("auth_uri"),
            region_name=conf.get("region_name"))
        nova.client.auth_token = keystone.auth_token
        nova.client.management_url = (
            keystone.service_catalog.url_for(
                service_type="compute"))
        return nova

    @property
    def glance(self):
        keystone = self.keystone
        from glanceclient.v1.client import Client as GlanceClient
        return GlanceClient(
            endpoint=self.strip_version(
                keystone.service_catalog.url_for(
                    service_type="image")),
            token=keystone.auth_token)

    @property
    def billing(self):
        keystone = self.keystone
        return nova_billing_heart_client.BillingHeartClient(
            management_url=keystone.service_catalog.url_for(
                service_type="nova-billing"))


def get_my_clients(tenant_id):
    conf = {
        'token': flask.session['keystone_unscoped']['access']['token']['id'],
        'auth_uri': flask.current_app.config['KEYSTONE_CONF']['auth_uri'],
        'tenant_id': tenant_id,
    }
    return ClientSet(**conf)

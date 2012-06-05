import flask

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
        return BillingHeartClient(
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
        from keystoneclient import service_catalog
        keystone = self.keystone
        endpoint = keystone.service_catalog.url_for(
            service_type="image")
        if endpoint.endswith("/"):
            endpoint = endpoint[:-1]
        if endpoint.endswith("/v1"):
            endpoint = endpoint[:-3]
        return Client(endpoint=endpoint, token=keystone.auth_token)


clients = ClientsSingleton()

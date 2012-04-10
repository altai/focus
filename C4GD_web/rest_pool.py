from C4GD_web import app
from models import *
from utils import select_keys
from benchmark import benchmark
# import gevent
# from gevent import monkey
# monkey.patch_all()

class RestfulPool(object):
    collections = {}
    public_url = ""
    token = None

    def __init__(self, user, tenant):
        # get token, user-tenant are already checked for existence
        # and authorisation at this point
        self.user = user
        self.tenant = tenant
        self.token, self.public_url = self.authenticate(self.user, self.tenant)

    def authenticate(self, user, tenant):
        app.logger.info('Started pool authentication')
        rs = Token.find_valid().find(user_id=user.id, tenant_id=tenant.id)
        if rs.count():
            app.logger.info('Database has token')
            with benchmark('Obtaining token from the database'):
                # the database contains token for our user
                # we take token and public url for Nova from db
                def get_token():
                    return rs.one()

                def get_public_url():                
                    tenant_id_template_in_use = g.store.find(
                        EndpointTemplate,
                        EndpointTemplate.public_url.like(u'%tenant_id%')).count() > 0
                    if tenant_id_template_in_use:
                        subselect = Select(
                            EndpointTemplate.id,
                            where=And(
                                EndpointTemplate.enabled==True,
                                EndpointTemplate.public_url.contains_string(
                                    u'tenant_id')))
                        endpoint = g.store.find(
                            Endpoint,
                            Endpoint.endpoint_template_id.is_in(subselect),
                            tenant_id=tenant.id).one()
                    else:
                        endpoint = g.store.find(Endpoint, tenant_id=tenant.id).one()
                    public_url = endpoint.endpoint_template.public_url.replace(
                        u'%tenant_id%', 
                        unicode(tenant.id))
                    return public_url
                return get_token(), get_public_url()
        else:
            app.logger.info('Obtaining token')
            # the database does not store valid token
            # ask Keystone RESTful API to generate a token
            # it returns public_url for Nova in the same response
            # no need to fetch it from the database
            key = user.credentials.find(tenant_id=tenant.id)\
                .values(Credential.key).next()
            # keys can have  tenant name appended (concatenated with ':')
            if u':' in key:
                key = key.split(u':')[0]
            with benchmark('Getting token via REST'):
                request_data = json.dumps({
                    'auth': {
                        'passwordCredentials': {
                            'username': g.user.name,
                            'password': key},
                        'tenantId': tenant.id}})
                response = requests.post(
                    'http://172.18.41.1:5000/v2.0/tokens', # TODO: to config
                    data=request_data,
                    headers = {'content-type': 'application/json'})
            assert 200 <= response.status_code < 300
            response_data = json.loads(response.text)
            token_id, public_url = response_data['access']['token']['id'],\
                response_data['access']['serviceCatalog'][0]['endpoints'][0]\
                    ['publicURL']
            token = g.store.get(Token, token_id)
        return token, public_url


    def __call__(self, method, *args, **kwargs):
        """
        Asks public url in a way the method wants, converts response into
        objects and attachs objects to self.collections.

        """
        assert len(self.public_url)
        klass = method.im_self
        verbose_name = '%s' % klass.__name__ + '.' + method.__name__

        response_handler = None
        kw = {}
        if method.two_phase:
            d, response_handler = method(*args, **kwargs)
            kw = {
                'params' if method.http_method == 'get' else 'data': \
                    json.dumps(d)}
        elif method.silent:
            pass
        else:
            response_handler = method
        app.logger.debug(kw)

        with benchmark('Total %s' % verbose_name):
            with benchmark('HTTP only %s' % verbose_name):
                request_url = self.public_url + klass.path + method.path.format(*args, **kwargs)
                response = requests.request(
                    method.http_method,
                    request_url,
                    headers={
                        'X-Auth-Project-Id': str(self.tenant.id),
                        'X-Auth-Token': self.token.id,
                        'Content-Type': 'application/json',
                        'X-Tenant-Name': self.tenant.name},
                    **kw)
            assert 200 <= response.status_code < 300
            app.logger.debug(response.text)
            if response_handler is not None:
                response_data = json.loads(response.text)
                objects = self.attach(
                    klass,
                    response_handler(response_data, *args, **kwargs) or [])
                if not method.is_plural:
                    if len(objects) == 1:
                        return objects[0]
                return objects
            
    def attach(self, klass, objects):
        if klass not in self.collections:
            self.collections[klass] = {}
        ids = []
        for obj in objects:
            self.collections[klass][obj.get_key()] = obj
            ids.append(obj.get_key())
        return list(select_keys(self.collections[klass], ids))


def get_pool(user, tenant):
    return RestfulPool(user, tenant)

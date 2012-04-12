import gevent
import json # will fail in <2.6, use Flask's?
import requests

from C4GD_web import app
from C4GD_web.benchmark import benchmark
from storm.locals import *
from orm import *
from flask import g
from utils import select_keys

# TODO: 
# - rename collctions to cache
# - add find() and get() methods to pool to mimic Storm
# - make find() and get() look in cache first, then use list() and get() models
# - traverse data of new objects and convert all atttributes with names ending with "_id" to int() if possible


def classmethod_verbose_name(method):
    klass = method.im_self
    return'%s' % klass.__name__ + '.' + method.__name__

class RestfulException(Exception): pass

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

                def get_public_url(store):                
                    tenant_id_template_in_use = store.find(
                        EndpointTemplate,
                        EndpointTemplate.public_url.like(u'%tenant_id%')).count() > 0
                    if tenant_id_template_in_use:
                        subselect = Select(
                            EndpointTemplate.id,
                            where=And(
                                EndpointTemplate.enabled==True,
                                EndpointTemplate.public_url.contains_string(
                                    u'tenant_id')))
                        endpoint = store.find(
                            Endpoint,
                            Endpoint.endpoint_template_id.is_in(subselect),
                            tenant_id=tenant.id).one()
                    else:
                        endpoint = store.find(Endpoint, tenant_id=tenant.id).one()
                    public_url = endpoint.endpoint_template.public_url.replace(
                        u'%tenant_id%', 
                        unicode(tenant.id))
                    return public_url
                gr1 = gevent.spawn(get_token)
                gr2 = gevent.spawn(get_public_url, g.store)
                gevent.joinall([gr1, gr2])
                return gr1.value, gr2.value
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

    def prepare_call(self, method, *args, **kwargs):
        """
        Accept classmethod of RESTful model and args/kwargs for it.
        Return tuple: HTTP method, URL, kwargs for requests.request(), response handler, plural, method klass.
        """
        assert hasattr(method, 'http_method'), 'Missing HTTP method decorator'
        assert hasattr(method, 'phase'), 'Missing phase decorator'
        assert hasattr(method, 'im_self'), 'Missing classmethod'
        klass = method.im_self
        request_url = self.public_url + klass.path + \
            method.path.format(*args, **kwargs)
        if method.http_method in ('post', 'put'):
            kw_arg_name = 'data'
        elif method.http_method in ('get', 'delete'):
            kw_arg_name = 'params'
        else:
            # definition of request argument name required
            raise RuntimeError, 'Unknown HTTP method "%s"' % method.http_method
        kw = {}
        response_handler = None
        if method.phase == 1:
            # request data required, no response handling
            kw[kw_arg_name] = method(*args, **kwargs)
        elif method.phase == 2:
            # no request data required, only response handling required
            response_handler = method
        elif method.phase == 3:
            # both request data and response handling required
            kw[kw_arg_name], response_handler = method(*args, **kwargs)
        elif method.phase == 4:
            # no request data or response handling required
            pass
        if kw_arg_name in kw:
            kw[kw_arg_name] = json.dumps(kw[kw_arg_name])
        return method.http_method, request_url, kw, response_handler, \
            getattr(method, 'is_plural', False), klass
 
    def handle_call(self, response_text, response_handler, is_plural, klass, *args, **kwargs):
        """
        Accept response text and response handler.
        Return list of RESTful model objects.
        """
        response_data = json.loads(response_text)
        objects = self.attach(
            klass,
            response_handler(response_data, *args, **kwargs) or [])
        if not is_plural:
            if len(objects) == 1:
                return objects[0]
        return objects
    
    def get_errors(self, response):
        if not(200 <= response.status_code < 300):
            try:
                error_message = json.loads(response.text)["badRequest"]["message"]
            except:
                error_message = response.text
            return [error_message]
        return []

    def call_one(self, method, *args, **kwargs):
        result = None
        http_method, request_url, kw, response_handler, is_plural, klass = \
            self.prepare_call(method, *args, **kwargs)
        benchmark_name = 'HTTP for %s' % \
            classmethod_verbose_name(method)
        app.logger.debug('%s %s %s %s %s', classmethod_verbose_name(method), http_method, request_url, self.headers(), kw)
        with benchmark(benchmark_name):
            response = requests.request(
                http_method,
                request_url,
                headers=self.headers(),
                **kw)
        errors = self.get_errors(response)
        if errors:
            raise RestfulException(errors)
        if response_handler:
            result = self.handle_call(
                response.text, response_handler, is_plural, klass, *args, **kwargs)
        return result

    def headers(self):
        return {
            'X-Auth-Project-Id': str(self.tenant.id),
            'X-Auth-Token': self.token.id,
            'Content-Type': 'application/json',
            'X-Tenant-Name': self.tenant.name}

    def __call__(self,  method_or_data, *args, **kwargs):
        """
        Asks public url in a way the method wants, converts response into
        objects and attachs objects to self.collections.

        """
        assert len(self.public_url)
        if type(method_or_data) is list:
            # return map(self.call_one, method_or_data)
            from requests import async
            prepared = map(self.prepare_call, method_or_data)
            async_rs = [
                requests.async.request(
                    x[0], # http method
                    x[1], # url
                    headers=self.headers(),
                    **x[2] # keyword args for request: params or data
                    ) for x in prepared]
            benchmark_name = 'HTTP for %s' % ", ".join(
                map(classmethod_verbose_name, method_or_data))
            with benchmark(benchmark_name):
                responses = requests.async.map(async_rs)
            errors = map(self.get_errors, responses)
            if any(errors):
                flat_errors_list = reduce(lambda acc, n: acc + n, errors, [])
                raise RestfulException(flat_errors_list)
            # TODO: handle only handlable
            return [
                self.handle_call(r.text, *a) for r, a in zip(
                    responses, map(lambda x: (x[3], x[4], x[5]), prepared))
                ]
        else:
            return self.call_one(method_or_data, *args, **kwargs)

            
    def attach(self, klass, objects):
        if klass.__name__ not in self.collections:
            self.collections[klass.__name__] = {}
        ids = []
        for obj in objects:
            self.collections[klass.__name__][obj.get_key()] = obj
            ids.append(obj.get_key())
        return list(select_keys(self.collections[klass.__name__], ids))


def get_pool(user, tenant):
    return RestfulPool(user, tenant)

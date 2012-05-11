# coding=utf-8
import sys
import gevent
import json # will fail in <2.6, use Flask's?
import requests

from flask import g, session

from storm.locals import *

from C4GD_web import app
from C4GD_web.benchmark import benchmark
from C4GD_web.utils import select_keys, obtain_scoped, get_public_url

from orm import *

from exceptions import InconsistentDatabaseException
from storm.exceptions import NotOneError


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

    def __init__(self, user, tenant_id, public_url=None):
        # get token, user-tenant are already checked for existence
        # and authorisation at this point
        self.user = user
        self.tenant_id = tenant_id
        self.token_id, nova_public_url = self.authenticate(
            self.user, self.tenant_id)

        self.public_url = public_url if public_url else nova_public_url
        


    def refresh(self):
        self.token_id, self.public_url = self.authenticate(self.user, self.tenant)

    @staticmethod
    def save_token(user_name, password):
        with benchmark('Getting token via REST'):
            request_data = json.dumps({
                'auth': {
                    'passwordCredentials': {
                        'username': user_name,
                        'password': password
                    },
                }
            })
            response = requests.post(
                    '%s/tokens' % app.config['KEYSTONE_URL'],
                    data=request_data,
                    headers = {'content-type': 'application/json'})
        if not (200 <= response.status_code < 300):
            return False
        response_data = json.loads(response.text)
        session["keystone_unscoped"] = response_data
        return True

    def authenticate(self, user, tenant_id):
        if tenant_id not in session['keystone_scoped']:
            obtain_scoped(tenant_id)
        return (
            session['keystone_scoped'][tenant_id]['access']['token']['id'],
            get_public_url(tenant_id))

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
        if kw_arg_name in kw and method.http_method in ('post', 'put'):
            kw[kw_arg_name] = json.dumps(kw[kw_arg_name])
        return method.http_method, request_url, kw, response_handler, \
            getattr(method, 'is_plural', False), klass
 
    def handle_call(self, response_text, response_handler, is_plural, klass, *args, **kwargs):
        """
        Accept response text and response handler.
        Return list of RESTful model objects.
        """
        with benchmark('Overall hand_call()'):
            with benchmark('JSON loaded in'):
                response_data = json.loads(response_text)
            with benchmark('Objects attached in'):
                objects = self.attach(
                    klass,
                    response_handler(response_data, *args, **kwargs) or [])
            with benchmark('result built in'):
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
        with benchmark('preparing'):
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
                config={'verbose': sys.stderr},
                **kw)
        errors = self.get_errors(response)
        if errors:
            raise RestfulException(errors)
        if response_handler:
            with benchmark('handling took'):
                with benchmark('response text in'):
                    text = response.content
                with benchmark('call itself'):
                    result = self.handle_call(
                        text, response_handler, is_plural,
                        klass, *args, **kwargs)
        return result

    def headers(self):
        return {
            'X-Auth-Project-Id': str(self.tenant_id),
            'X-Auth-Token': self.token_id,
            'Content-Type': 'application/json'}

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
            with benchmark('handling'):
                return [
                    self.handle_call(r.text, *a) for r, a in zip(
                        responses, map(lambda x: (x[3], x[4], x[5]), prepared))
                    ]
        else:
            with benchmark('calling one'):
                return self.call_one(method_or_data, *args, **kwargs)

            
    def attach(self, klass, objects):
        with benchmark('attaching'):
            if klass.__name__ not in self.collections:
                self.collections[klass.__name__] = {}
            ids = []
            for obj in objects:
                self.collections[klass.__name__][obj.get_key()] = obj
                ids.append(obj.get_key())
            return list(select_keys(self.collections[klass.__name__], ids))



def get_pool(user, tenant, public_url=None):
    return RestfulPool(user, tenant, public_url)

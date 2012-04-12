# TODO: create base class for RESTful objects
# TODO: create a client Tenant to work with RESTful API
# TODO: make client reconnecting and regenerating tokens when required
# HINT: tenant client can work in a way similar to STORM Store
# HINT: objects returned by the client must work smoothly with models
from flask import g

from C4GD_web import app

from decorators import *
from utils import select_keys


__all__ = ['VirtualMachine', 'Image', 'Flavor', 'KeyPair', 'SecurityGroup']


class RESTModelBase(object):
    _key_name = 'id'
    
    def __init__(self, d):
        for k, v in d.items():
            setattr(self, k, v)

    def get_key(self):
        return getattr(self, self._key_name)


class VirtualMachine(RESTModelBase):
    path = '/servers'

    @classmethod
    @back
    @plural
    @get('/detail')
    def list(cls, data, bypass=None, *a, **kw):
        servers = data['servers']
        if bypass is not None:
            assert callable(bypass)
            servers = filter(bypass, servers)
        return map(cls, servers)

    @classmethod
    @forth
    @post('')
    def spawn(cls, *args, **kwargs):
        d = args[0]
        image = g.pool.collections['Image'][int(d['image'])]
        result = {
            'server': {
                'name': d['name'],
                'imageRef': image.links[0]['href'],
                'flavorRef': int(d['flavor'])
                }
             }
        if 'password' in d and d['password']:
            result['server']['adminPass'] = d['password']
        if 'keypair' in d:
            result['server']['key_name'] = d['keypair']
        if 'security_groups':
            security_group_keys = d.getlist('security_groups')
            if len(security_group_keys):
                security_groups = select_keys(
                    g.pool.collections['SecurityGroup'],
                    map(int, security_group_keys))            
                result['server']['security_groups'] = [
                    {'name': x.name} for x in security_groups]
        return result

    @classmethod
    @blind
    @delete('/{0}')
    def remove(cls): pass

    @classmethod
    @back
    @get('/{0}')
    def get(cls, data, *args, **kwargs):
        return [cls(data['server'])]

    
class Image(RESTModelBase):
    path = '/images'
    
    @classmethod
    @back
    @plural
    @get('')
    def list(cls, data, *a, **kw):
        def int_id(x):
            x['id'] = int(x['id'])
            return x
        return map(cls, filter(int_id, data['images']))

class Flavor(RESTModelBase):
    path = '/flavors'
    
    @classmethod
    @back
    @plural
    @get('/detail')
    def list(cls, data, *a, **kw):
        return map(cls, data['flavors'])


class KeyPair(RESTModelBase):
    path = '/os-keypairs'
    _key_name = 'name'

    @classmethod
    @back
    @plural
    @get('')
    def list(cls, data, *a, **kw):
        return [cls(x['keypair']) for x in data['keypairs']]


class SecurityGroup(RESTModelBase):
    path = '/os-security-groups'
    
    @classmethod
    @back
    @plural
    @get('', is_plural=True)
    def list(cls, data, *a, **kw):
        return map(cls, data['security_groups'])

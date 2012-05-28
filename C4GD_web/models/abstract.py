import functools

from flask import session, current_app

import requests

from C4GD_web import exceptions
from C4GD_web import utils


class Base(object):
    class NotFound(Exception): pass
    # raise
    @classmethod
    def list(cls, *args, **kwargs): raise NotImplementedError

    @classmethod
    def get(cls, obj_id): raise NotImplementedError

    @classmethod
    def delete(cls, obj_id): raise NotImplementedError

    @classmethod
    def create(cls, *args, **kwargs): raise NotImplementedError

    @classmethod
    def update(cls, obj_id): raise NotImplementedError


class OpenstackListMixin(object):
    @classmethod
    def list(cls, *args, **kwargs):
        """
        Gets list data representing requested objects.
        We either have tenant_id passed in as kwarg or return data for all 
        tenants concatenated. Response is usually a dictionary with one key and
        an array corresponding to that list.
        404 considered an error here.

        :: params
        """
        acc = []
        def haul(response):
            acc.extend(cls.list_accessor(response))
        path = cls.base + getattr(cls, 'list_prefix', '')
        if 'tenant_id' in kwargs:
            tenant_id = kwargs['tenant_id']
            del(kwargs['tenant_id'])
        else:
            tenant_id = None
        snap = functools.partial(
            cls._snap,
            path=path,
            success=haul,
            params=kwargs,
            api_func=functools.partial(
                utils.openstack_api_call,
                cls.service_type,
                http_method=requests.get)) 
        if tenant_id is not None:
            snap(tenant_id)
        else:
            for tenant in cls._tenants(**kwargs):
                snap(tenant['id'])
                if getattr(cls, 'list_any_one_tenant', False):
                    break
        return acc

class OpenstackMixinBase(object):
    @classmethod
    def _call(cls, obj_id, tenant_id, prefix, http_method, **kwargs):
        path = '%s%s/%s' % (
            cls.base,
            getattr(cls, prefix, ''),
            obj_id)
        snap = functools.partial(
            cls._snap,
            path=path,
            params=kwargs,
            api_func=functools.partial(
                utils.openstack_api_call,
                cls.service_type,
                http_method=http_method))
        if tenant_id is not None:
            return snap(tenant_id)
        else:
            for tenant in cls._tenants(**kwargs):
                return snap(tenant['id'])
        raise cls.NotFound

    @staticmethod
    def _snap(tenant_id, path, success=None, tolerate404=True, api_func=False, **kw):
        """
        Used when we uncertain what tenant is correct for an object
        """
        assert api_func, 'snap() was used directly without api_func'
        try:
            trophy = api_func(tenant_id, path, **kw)
        except exceptions.GentleException, e:
            if tolerate404:
                if e.args[1].status_code == 404:
                    pass
                else:
                    raise
            else:
                raise
        else:
            if success is None:
                return trophy
            else:
                success(trophy)

    @staticmethod
    def _tenants(**kwargs):
        """
        Utility to list tenants for user.
        """
        if 'tenants' in kwargs:
            return kwargs['tenants']
        else:
            return session['tenants']['tenants']['values']


class OpenstackDeleteMixin(object):
    @classmethod
    def delete(cls, obj_id, tenant_id=None):
        """
        Deletes object by id.
        """
        return cls._call(obj_id, tenant_id, 'delete_prefix', requests.delete)
        

class OpenstackGetMixin(object):
    @classmethod
    def get(cls, obj_id, tenant_id=None, **kwargs):
        """
        Gets an object by id.
        Accepts useful hint about what tenant requested object belongs to.
        If hint is missing iterates through tenants to find the obj.
        In the second case 404 is not an error because Nova API returns 404
        for both unknown path and object requested in incorrect tenant.
        """
        return cls._call(obj_id, tenant_id, 'get_prefix', requests.get)


class OpenstackAPI(OpenstackMixinBase, OpenstackListMixin, OpenstackGetMixin, OpenstackDeleteMixin, Base): 
    pass


class NovaAPI(OpenstackAPI):
    service_type = 'compute'


class GlanceAPI(OpenstackAPI):
    service_type = 'image'


class Image(GlanceAPI):
    base = '/images'
    list_any_one_tenant = True

    @staticmethod
    def list_accessor(obj):
        return obj['images']


class VirtualMachine(NovaAPI):
    base = '/servers'
    list_prefix = '/detail'

    @staticmethod
    def list_accessor(obj):
        return obj['servers']

    @classmethod
    def create(cls, tenant_id, name, image, flavor, 
               password=None, keypair=None, security_groups=[]):
        image = Image.get(int(image))
        request_data = {
            'server': {
                'name': name,
                'imageRef': image['image']['links'][0]['href'],
                'flavorRef': int(flavor)
                }
            }
        if password:
            request_data['server']['adminPass'] = password
        if keypair:
            request_data['server']['key_name'] = keypair
        if len(security_groups):
            request_data['server']['security_groups'] = utils.select_keys(
                SecurityGroup.list(),
                map(int, security_group_keys))
        utils.openstack_api_call(tenant_id, cls.base, request_data, service_type=cls.service_type, http_method=requests.post)


class Flavor(NovaAPI):
    base = '/flavors'
    list_prefix = '/detail'
    list_any_one_tenant = True

    @staticmethod
    def list_accessor(obj):
        return obj['flavors']


class KeyPair(NovaAPI):
    base = '/os-keypairs'
    list_any_one_tenant = True

    @staticmethod
    def list_accessor(obj):
        return obj['keypairs']


class SecurityGroup(NovaAPI):
    base = '/os-security-groups'
    list_any_one_tenant = True

    @staticmethod
    def list_accessor(obj):
        return obj['security_groups']


class AccountBill(Base):
    @classmethod
    def list(cls):
        return utils.billing_get('/account')

    @classmethod
    def get(cls, account_id, **kwargs):
        request_data = {
                'account_name': account_id,
        }

        for x in 'time_period', 'period_start', 'period_end':
            if kwargs.get(x) is not None:
                request_data[x] = kwargs[x]
        
        return utils.billing_get('/report', params=request_data)['accounts']


class Volume(NovaAPI):
    base = '/gd-local-volumes'

    @staticmethod
    def list_accessor(obj):
        return obj['volumes']


class Tariff(Base):
    @classmethod
    def list(cls):
        return utils.billing_get('/tariff')


class SSHKey(NovaAPI):
    base = '/os-keypairs'
    list_any_one_tenant = True

    @staticmethod
    def list_accessor(r):
        return [x['keypair'] for x in r['keypairs']]

    @classmethod
    def create(cls, name, public_key):
        if public_key:
            cls.register(name, public_key)
        else:
            # returns private key
            return cls.generate(name)

    @classmethod
    def register(cls, name, public_key):
        request = {
            "keypair": {
                "name": name,
                "public_key": public_key
            }
        }
        for tenant in cls._tenants():
            result = cls._snap(
                tenant['id'],
                cls.base,
                api_func=functools.partial(
                    utils.openstack_api_call,
                    cls.service_type,
                    http_method=requests.post),
                params=request)
            if result != None:#some tenant allowed to post
                return
        raise RuntimeError, 'No tenant to post'

    @classmethod
    def generate(cls, name):
        request = {
            "keypair": {
                "name": name
            }
        }
        for tenant in cls._tenants():
            result = cls._snap(
                tenant['id'],
                cls.base,
                api_func=functools.partial(
                    utils.openstack_api_call,
                    cls.service_type,
                    http_method=requests.post),
                params=request)
            if result != None:#some tenant allowed to post
                return result["keypair"]
        raise RuntimeError, 'No tenant to post'

    @classmethod
    def get(cls, keypair_name):
        for keydata in cls.list():
            if keypair_name == keydata['name']:
                return keydata

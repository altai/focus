# TODO(apugachev) replace use of these by aababilov client's calls
import datetime
import functools
import httplib
import os
import urlparse
import requests

import flask

from C4GD_web import clients
from C4GD_web import exceptions
from C4GD_web import utils


class Base(object):
    class NotFound(Exception):
        pass

    @classmethod
    def list(cls, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def get(cls, obj_id):
        raise NotImplementedError

    @classmethod
    def delete(cls, obj_id):
        raise NotImplementedError

    @classmethod
    def create(cls, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def update(cls, obj_id):
        raise NotImplementedError


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
            for tenant_id in cls._tenants(**kwargs):
                snap(tenant_id)
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
            for tenant_id in cls._tenants(**kwargs):
                return snap(tenant_id)
        raise cls.NotFound, '%s with ID %s not found.' % (cls.__name__, obj_id)

    @staticmethod
    def _snap(tenant_id, path, success=None, tolerate404=True, api_func=False,
              **kw):
        """
        Used when we uncertain what tenant is correct for an object
        """
        assert api_func, 'snap() was used directly without api_func'
        try:
            trophy = api_func(tenant_id, path, **kw)
        except exceptions.GentleException, e:
            if tolerate404:
                if len(e.args) > 1 and e.args[1].status_code == 404:
                    pass
                elif e.args[0].startswith('No public URL'):
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

        If kwargs contain explicit tenant dict return it as a signle-item list.
        If session contains tenants return list of tenant ids from session.
        Return default tenant id from session.
        """
        if 'tenants' in kwargs:
            return [x['id'] for x in kwargs['tenants']]
        else:
            tenants = [x['id'] for x in flask.session['tenants']]
            if len(tenants):
                return tenants
        return [clients.get_systenant_id()]


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


class OpenstackAPI(OpenstackMixinBase, OpenstackListMixin, OpenstackGetMixin,
                   OpenstackDeleteMixin, Base):
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

    @classmethod
    def create(cls, tenant_id, name, container_format, disk_format, path,
               public=True, architecture='x86_64', kernel_id=None,
               ramdisk_id=None):
        """Upload image to Glance API.

        Prepare headers.
        - content type application/octet-stream
        - image size
        Post request with file content as body.
        Return image dict.
        """
        properties = {
            'image_state': 'available',
            'project_id': tenant_id,
            'architecture': architecture,
            'image_location': 'local'}
        if kernel_id:
            properties['kernel_id'] = int(kernel_id)
        if ramdisk_id:
            properties['ramdisk_id'] = int(ramdisk_id)
        kwargs = {
            'name': name,
            'disk_format': disk_format,
            'container_format': container_format,
            'size': str(os.path.getsize(path)),
            'is_public': str(public),
            'properties': properties}
        image = clients.user_clients(tenant_id).image.images.create(
            **kwargs)
        return image._info


def get_connection_type(scheme):
    """
    Returns the proper connection type
    """
    if scheme == 'https':
        return httplib.HTTPSConnection
    else:
        return httplib.HTTPConnection


def get_status_code(response):
    """
    Returns the integer status code from the response, which
    can be either a Webob.Response (used in testing) or httplib.Response
    """
    if hasattr(response, 'status_int'):
        return response.status_int
    else:
        return response.status


class NovaImage(NovaAPI):
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
    def create(cls, tenant_id, name, image_id, flavor_id,
               password=None, keypair=None, security_groups=[]):

        image = NovaImage.get(image_id)
        try:
            imageRef = [
                x['href'] for x in image['image']['links'] if
                x['rel'] == u'self'
            ][0]
        except KeyError:
            raise RuntimeError('API returns image without link `self`', image)
        request_data = {
            'server': {
                'name': name,
                'imageRef': imageRef,
                'flavorRef': flavor_id
            }
        }
        if password:
            request_data['server']['adminPass'] = password
        if keypair:
            request_data['server']['key_name'] = keypair
        if len(security_groups):
            request_data['server']['security_groups'] = [
                {'name': x['name']} for x in SecurityGroup.list()
                if x['id'] in security_groups
            ]
        utils.openstack_api_call(
            cls.service_type, tenant_id, cls.base, request_data,
            http_method=requests.post)

    @classmethod
    def reboot(cls, tenant_id, vm_id, type):
        utils.openstack_api_call(
            cls.service_type,
            tenant_id,
            '%s/%s/action' % (cls.base, vm_id),
            {'reboot': {'type': type}},
            requests.post)


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


class Volume(NovaAPI):
    base = '/gd-local-volumes'

    @staticmethod
    def list_accessor(obj):
        return obj['volumes']


class SSHKey(NovaAPI):
    base = '/os-keypairs'
    list_any_one_tenant = True

    @staticmethod
    def list_accessor(r):
        return [x['keypair'] for x in r['keypairs']]

    @classmethod
    def create(cls, **kwargs):
        name, public_key = list(
            utils.select_keys(kwargs, ('name', 'public_key'), True))
        if public_key:
            cls.register(name, public_key)
        else:
            # returns private key
            return cls.generate(name)

    @classmethod
    def register(cls, name, public_key):
        request = {
            'keypair': {
                'name': name,
                'public_key': public_key
            }
        }
        for tenant_id in cls._tenants():
            result = cls._snap(
                tenant_id,
                cls.base,
                api_func=functools.partial(
                    utils.openstack_api_call,
                    cls.service_type,
                    http_method=requests.post),
                params=request)
            if result is not None:
                # some tenant allowed to post, we can return
                return
        raise RuntimeError('No tenant to post')

    @classmethod
    def generate(cls, name):
        request = {
            'keypair': {
                'name': name
            }
        }
        for tenant_id in cls._tenants():
            result = cls._snap(
                tenant_id,
                cls.base,
                api_func=functools.partial(
                    utils.openstack_api_call,
                    cls.service_type,
                    http_method=requests.post),
                params=request)
            if result is not None:
                return result['keypair']
        raise RuntimeError('No tenant to post')

    @classmethod
    def get(cls, keypair_name):
        for keydata in cls.list():
            if keypair_name == keydata['name']:
                return keydata

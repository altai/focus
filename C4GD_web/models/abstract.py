from flask import session, current_app

from C4GD_web.benchmark import benchmark
from C4GD_web.exceptions import GentleException, BillingAPIError
from C4GD_web.utils import nova_get, nova_post, nova_delete, select_keys, \
    response_ok, billing_get


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
    def create(cls, obj_id): raise NotImplementedError

    @classmethod
    def update(cls, obj_id): raise NotImplementedError


class NovaAPIListMixin(object):
    @classmethod
    def list(cls, *args, **kwargs):
        """
        Gets list data representing requested objects.
        We either have tenant_id passed in as kwarg or return data for all 
        tenants concatenated. Response is usually a dictionary with one key and
        an array corresponding to that list.
        404 considered an error here.
        """
        acc = []
        def haul(nova_response):
            acc.extend(cls.list_accessor(nova_response))
        path = cls.base + getattr(cls, 'list_prefix', '')
        if 'tenant_id' in kwargs:
            cls.snap(kwargs['tenant_id'], path, success=haul)
        else:
            tenant_ids = [tenant['id'] for tenant in cls.tenants(**kwargs)]
            if len(tenant_ids):
                if getattr(cls, 'list_any_one_tenant', False):
                    tenant_id = tenant_ids[0]
                    cls.snap(tenant_id, path, success=haul)
                else:
                    for tenant_id in tenant_ids:
                        cls.snap(tenant_id, path, success=haul)
        return acc


class NovaAPIDeleteMixin(object):
    @classmethod
    def delete(cls, obj_id, tenant_id=None):
        """
        Deletes object by id.
        """
        path = '%s%s/%s' % (
            cls.base,
            getattr(cls, 'delete_prefix', ''),
            obj_id)
        if tenant_id is not None:
            return cls.snap(tenant_id, path, api_func=nova_delete)
        else:
            for tenant in cls.tenants(**kwargs):
                return cls.snap(tenant['id'], path, api_func=nova_delete)
        raise cls.NotFound
        

class NovaAPIGetMixin(object):
    @classmethod
    def get(cls, obj_id, tenant_id=None, **kwargs):
        """
        Gets an object by id.
        Accepts useful hint about what tenant requested object belongs to.
        If hint is missing iterates through tenants to find the obj.
        In the second case 404 is not an error because Nova API returns 404
        for both unknown path and object requested in incorrect tenant.
        """
        path = '%s%s/%s' % (
            cls.base,
            getattr(cls, 'get_prefix', ''),
            obj_id)
        if tenant_id is not None:
            return cls.snap(tenant_id, path)
        else:
            for tenant in cls.tenants(**kwargs):
                return cls.snap(tenant['id'], path)
        raise cls.NotFound


class NovaSnapMxn(object):
    @staticmethod
    def snap(tenant_id, path, success=None, tolerate404=True, api_func=nova_get):
        """
        Used when we uncertain what tenant is correct for an object
        """
        try:
            trophy = api_func(tenant_id, path)
        except GentleException, e:
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
    def tenants(**kwargs):
        """
        Utility to list tenants for user.
        """
        if 'tenants' in kwargs:
            return kwargs['tenants']
        else:
            return session['tenants']['tenants']['values']


class NovaAPI(
    NovaSnapMxn, NovaAPIListMixin, NovaAPIGetMixin, NovaAPIDeleteMixin, Base):
    pass


class Image(NovaAPI):
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
            request_data['server']['security_groups'] = select_keys(
                SecurityGroup.list(),
                map(int, security_group_keys))
        nova_post(tenant_id, cls.base, request_data)


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
        return billing_get('/account')

    @classmethod
    def get(cls, account_id, **kwargs):
        request_data = {
                'account': account_id,
        }

        for x in 'time_period', 'period_start', 'period_end':
            if kwargs.get(x) is not None:
                request_data[x] = kwargs[x]
        
        return billing_get('/bill', params=request_data)

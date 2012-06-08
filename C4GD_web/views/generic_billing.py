import copy
from datetime import date

from flask import g, current_app, url_for
from flask import g, request, session
from flask import jsonify

from C4GD_web.models.abstract import Tariff
from C4GD_web.models.orm import get_store, Tenant
from C4GD_web.models.abstract import AccountBill, VirtualMachine, Image, Volume
from C4GD_web.models.orm import User, Tenant, get_store
from C4GD_web.utils import billing_get



class Dataset(object):
    def __init__(self, params=None, delayed=False, user_id=None, tenant_id=None):
        self.data = account_bill_show(
            params.account_id, user_id, tenant_id,
            period_start=params.period_start,
            period_end=params.period_end,
            time_period=params.time_period)


class Params(object):
    period_start = None
    period_end = None
    time_period = None

    def __init__(self, account_id, args={}):
        self.account_id = account_id
        if 'period_start' in args and 'period_end' in args:
            # control format of dates
            self.period_start = args['period_start']
            self.period_end = args['period_end']
        else:
            kind = args.get('kind', 'month')
            if kind == 'today':
                self.time_period = date.today().isoformat()
            elif kind == 'month':
                pass# API default is this month
            elif kind == 'year':
                self.time_period = date.today().year
            
    def lookup_key(self):
        return '%s:%s:%s:%s' % (
            self.account_id, self.period_start,
            self.period_end, self.time_period)


def _calc_cost(res):
    '''
    Currently one level of folded data.
    '''
    cost = res.get("cost", 0.0)
    for child in res.get("children", ()):
        cost += _calc_cost(child)
    return cost
    res["cost"] = cost


def _compact_bill(resources):
    '''
    Return list of resources which do not have parents, in descending 
    chronological order.
    Resourced with parents must be grouped under their parents.
    Cost must be calculated for parents based on their children cost.
    '''
    # build dict of resources
    res_by_id = {}
    for res in resources:
        res_by_id[res['id']] = res
    # iterate through non-orphans
    for res in filter(lambda x: x['parent_id'] not in [None, 0], resources):
        #  add non-orphan to 'children' of it's parent in dict of resources
        parent = res_by_id[res['parent_id']]
        if not 'children' in parent:
            parent['children'] = []
        parent['children'].append(res)
    # iterate through orphans
    for res in filter(lambda x: x['parent_id'] in [None, 0], resources):
        orphan = res_by_id[res['id']]
        #  calculate cost based on children recorded in dict of resources
        #  change cost in resource in the dict
        orphan['cost'] = _calc_cost(orphan)
    # return orphans sorted chronologically
    return [res_by_id[res['id']] for res in sorted(
        filter(
                lambda x: x['parent_id'] in [None, 0],
                resources),
        key=lambda x: x['created_at'],
        reverse=True)]

                  
def _concentrate_resources(resources, tenant_id):
    '''
    For every orphan resource add verbose name and brief info url.
    '''
    def process(objs, model, endpoint):
        '''
        Nova does not return deleted servers.
        '''
        info = model.list()
        ref = dict([(x['name'], x) for x in objs])
        result = {}
        # some objs will lack detailed info. it is not a problem
        # it is solved during presentation to user
        informative = filter(lambda x: unicode(x['id']) in ref.keys(), info)
        if model is Volume:
            instances_info = dict([(x['id'], x) for x in VirtualMachine.list()])
            for x in informative:
                x['instance_info'] = instances_info[x['instance_id']]
        for x in informative:
            actual = copy.deepcopy(ref[unicode(x['id'])])
            actual['detailed'] = x
            actual['detailed']['focus_url'] = url_for(endpoint, obj_id=x['id'])
            result[(actual['id'], actual['rtype'])] = actual
        return result
    def filter_type(resource_type):
        return [x for x in resources if x['rtype'] == resource_type and x['parent_id'] is None]
    processors = (
        ('nova/instance', VirtualMachine, 'virtual_machines.show'),
        ('glance/image', Image, 'images.show'),
        ('nova/volume', Volume, 'volumes.show')
        )
    d = {}
    for rtype, model, endpoint in processors:        
        d.update(process(filter_type(rtype), model, endpoint))
    return [x if (x['id'], x['rtype']) not in d else d[(x['id'], x['rtype'])] for x in resources]


def account_bill_show(account_id, user_id, tenant_id, **kw):
    bill = AccountBill.get(account_id, **kw)[0] # list with tenant_id as ['name']
    bill['resources'] = _concentrate_resources(bill['resources'], tenant_id)
    bill['resources'] = _compact_bill(bill['resources'])
    return bill


def generic_billing(tenant, user, tenants=None):
    """
    On non-AJAX request return page and iniate process of getting of dataset for default parameters. Parameters can be different in the fragment history and the js app can request dataset with other parameters, but in most cases we will guess correctly.
    On AJAX call get dataset for requested parameter and return it in correct formatting as JSON response.
    """
    if request.is_xhr:
        p = Params(tenant.id, request.args)
        d = Dataset(p, user_id=user['id'], tenant_id=tenant.id)
        return jsonify({
            'caption': 'Billing for project %s' % tenant.name,
            'data': d.data
        })
    else:
        tariffs = Tariff.list()
        context = {
            'tenant_id': tenant.id,
            'tariffs': tariffs
            }
        if tenants is not None:
            context.update({
                'tenants': tenants
                })
        return context

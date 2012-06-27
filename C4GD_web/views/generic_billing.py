import copy
import datetime

import flask

from C4GD_web.models import abstract


class Dataset(object):
    def __init__(self, params=None, delayed=False, user_id=None,
                 tenant_id=None):
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
                self.time_period = datetime.date.today().isoformat()
            elif kind == 'month':
                # API default is this month
                pass
            elif kind == 'year':
                self.time_period = datetime.date.today().year

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
    return map(
        lambda res: res_by_id[res['id']],
        sorted(
            filter(
                lambda x: x['parent_id'] in [None, 0],
                resources),
            key=lambda x: x['created_at'],
            reverse=True))


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
        if model is abstract.Volume:
            instances_info = dict(
                [(x['id'], x) for x in abstract.VirtualMachine.list()])
            for x in informative:
                x['instance_info'] = instances_info[x['instance_id']]
        for x in informative:
            actual = copy.deepcopy(ref[unicode(x['id'])])
            actual['detailed'] = x
            actual['detailed']['focus_url'] = flask.url_for(
                endpoint, obj_id=x['id'])
            result[(actual['id'], actual['rtype'])] = actual
        return result

    def filter_type(resource_type):
        return filter(
            lambda x: x['rtype'] == resource_type and x['parent_id'] is None,
            resources
        )
    processors = (
        ('nova/instance', abstract.VirtualMachine, 'virtual_machines.show'),
        ('glance/image', abstract.Image, 'images.show'),
        ('nova/volume', abstract.Volume, 'volumes.show')
    )
    d = {}
    for rtype, model, endpoint in processors:
        d.update(process(filter_type(rtype), model, endpoint))
    return map(
        lambda x: d.get((x['id'], x['rtype']), x),
        resources)


def account_bill_show(account_id, user_id, tenant_id, **kw):
    # list with tenant_id as ['name']
    bill = abstract.AccountBill.get(account_id, **kw)[0]
    bill['resources'] = _concentrate_resources(bill['resources'], tenant_id)
    bill['resources'] = _compact_bill(bill['resources'])
    return bill


def generic_billing(tenant, user, tenants=None):
    """Used in project and global billing.

    On non-AJAX request return page.
    On AJAX call get dataset for requested parameters and return it
    in correct formatting as JSON response.
    """
    if flask.request.is_xhr:
        p = Params(tenant.id, flask.request.args)
        d = Dataset(p, user_id=user['id'], tenant_id=tenant.id)
        return flask.jsonify({
            'caption': 'Billing for project %s' % tenant.name,
            'data': d.data
        })
    else:
        tariffs = abstract.Tariff.list()
        context = {
            'tenant_id': tenant.id,
            'tariffs': tariffs
        }
        if tenants is not None:
            context.update({
                'tenants': tenants
            })
        return context

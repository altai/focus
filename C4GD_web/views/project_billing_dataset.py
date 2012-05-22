from datetime import date

from flask import g, current_app

from C4GD_web.models.abstract import AccountBill
from C4GD_web.models.orm import User, Tenant, get_store
from C4GD_web.utils import billing_get


class Dataset(object):
    def __init__(self, params=None, delayed=False, user_id=None, tenant_id=None):
        self.data = account_bill_show(
                params.account_id, user_id, tenant_id,
                current_app.config['BILLING_URL'],
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

def _build_resource_tree(bill):

    def get_resource_tree(resources):
        res_by_id = dict(((res["id"], res) for res in resources))
        for res in resources:
            try:
                parent = res_by_id[res["parent_id"]]
            except KeyError:
                pass
            else:
                parent.setdefault("children", []).append(res)
        return filter(
            lambda res: res["parent_id"] not in res_by_id,
            resources)

    def calc_cost(res):
        cost = res.get("cost", 0.0)
        for child in res.get("children", ()):
            calc_cost(child)
            cost += child["cost"]
        res["cost"] = cost

    for acc in bill:
        subtree = get_resource_tree(acc["resources"])
        acc_cost = 0.0
        for res in subtree:
            calc_cost(res)
            acc_cost += res["cost"]
        acc["cost"] = acc_cost
        acc["resources"] = subtree
    return bill


def _linear_bill(bill):
    linear_bill = []
    def print_res(res, depth):
        res["depth"] = depth        
        linear_bill.append(res)
        depth += 1
        for child in res.get("children", ()):
            print_res(child, depth)
        try:
            del res["children"]
        except KeyError:
            pass
        del res["parent_id"]

    for acc in bill:
        linear_bill = []
        for res in sorted(acc["resources"], 
                key=lambda res: (res["rtype"], res["name"])):            
            print_res(res, 0)
        acc["resources"] = linear_bill


def account_bill_show(account_id, user_id, tenant_id, public_url, **kw):
    bill = AccountBill.get(account_id, **kw)
    _linear_bill(_build_resource_tree(bill))
    return bill[0] if len(bill) else []


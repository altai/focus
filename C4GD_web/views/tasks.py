from celery.task import task
from C4GD_web.models import get_pool, AccountBill, User, Tenant, get_store


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


@task(ignore_result=True)
def account_bill_show(account_id, user_id, tenant_id, public_url, **kw):
#    return {
#        "cost": "66847115.25", "id": 5,
#        "resources": [
#            {"name": "103", "rtype": "glance/image", "created_at": "2012-04-24T11:53:43Z",
#              "destroyed_at": None, "depth": 0, "cost": "3.00", "id": 28222},
#            {"name": "104", "rtype": "nova/instance", "created_at": "2012-04-25T04:44:50Z",
#              "destroyed_at": None, "depth": 0, "cost": "14.00", "id": 28235},
#        ],
#    }
    
    # call Account.show and save result in db
    store = get_store('RO')
    user = store.get(User, user_id)
    tenant = store.get(Tenant, tenant_id)
    billing_pool = get_pool(user, tenant, public_url=public_url)
    # what db? what format? save it for future
    bill = [billing_pool(AccountBill.show, account_id=tenant.id, **kw).__dict__]
    _linear_bill(_build_resource_tree(bill))
    return bill[0]


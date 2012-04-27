from celery.task import task
from C4GD_web.models import get_pool, AccountBill, User, Tenant, get_store


@task(ignore_result=True)
def account_bill_show(account_id, user_id, tenant_id, public_url, **kw):
    # call Account.show and save result in db
    store = get_store('RO')
    user = store.get(User, user_id)
    tenant = store.get(Tenant, tenant_id)
    billing_pool = get_pool(user, tenant, public_url=public_url)
    # what db? what format? save it for furure
    bill = billing_pool(AccountBill.show, account_id=tenant.id, **kw)
    

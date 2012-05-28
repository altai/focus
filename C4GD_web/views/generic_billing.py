from flask import g, request, session
from flask import jsonify

from C4GD_web.models.abstract import Tariff
from C4GD_web.models.orm import get_store, Tenant

from .project_billing_dataset import Dataset, Params


def generic_billing(tenant_id, tenants=None):
    """
    On non-AJAX request return page and iniate process of getting of dataset for default parameters. Parameters can be different in the fragment history and the js app can request dataset with other parameters, but in most cases we will guess correctly.
    On AJAX call get dataset for requested parameter and return it in correct formatting as JSON response.
    """
    if request.is_xhr:
        p = Params(tenant_id, request.args)
        d = Dataset(p, user_id=g.user.id, tenant_id=tenant_id)
        try:
            tenant_name = session['keystone_scoped'][tenant_id]['access']['token']['tenant']['name']
        except KeyError:
            store = get_store('RO')
            tenant_name = store.get(Tenant, int(tenant_id)).name
        return jsonify({
            'caption': 'Billing for project %s' % tenant_name,
            'data': d.data
        })
    else:
        tariffs = Tariff.list()
        context = {
            'tenant_id': tenant_id,
            'tariffs': tariffs 
            }
        if tenants is not None:
            context.update({
                'tenants': tenants
                })
        return context

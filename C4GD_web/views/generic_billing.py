from flask import g, request, session
from flask import jsonify

from .project_billing_dataset import Dataset, Params


def generic_billing(tenant_id, tenants=None):
    """
    On non-AJAX request return page and iniate process of getting of dataset for default parameters. Parameters can be different in the fragment history and the js app can request dataset with other parameters, but in most cases we will guess correctly.
    On AJAX call get dataset for requested parameter and return it in correct formatting as JSON response.
    """

    if request.is_xhr:
        p = Params(tenant_id, request.args)
        d = Dataset(p, user_id=g.user.id, tenant_id=tenant_id)
        tenant_name = session['keystone_scoped'][tenant_id]['access']['token']['tenant']['name']
        return jsonify({
            'caption': 'Billing for project %s' % tenant_name,
            'data': d.data
        })
    else:
        context = {
            'tenant_id': tenant_id
            }
        if tenants is not None:
            context.update({
                'tenants': tenants
                })
        return context

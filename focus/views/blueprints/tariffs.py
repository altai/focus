"""List and update tariffs.

Restrict access of non-admin users.
"""
import sys

import flask
from flask import blueprints

from focus import clients
from focus.views import environments
from focus.views import forms
from focus.views import generic_billing


bp = environments.admin(blueprints.Blueprint('tariffs', __name__))


@bp.route('')
def index():
    """List tariffs"""
    tariffs = generic_billing.get_tariff_list()
    return {'tariffs': tariffs}


@bp.route('<path:name>/', methods=['GET', 'POST'])
def edit(name):
    """Edit tariff"""
    tariffs = generic_billing.get_tariff_list()
    # TODO(apugachev) - handle nonexisting tariff, KeyError in next line
    form = forms.TariffEditForm(price=tariffs.get(name, 1.0))
    if form.validate_on_submit():
        try:
            response = clients.admin_clients().billing.tariff.update(
                name,
                form.price.data,
                form.migrate.data)
        except Exception, e:
            flask.flash(
                'Failed to update tariff. Error: %s' % e.args[0],
                'error')
            exc_type, exc_value, tb = sys.exc_info()
            flask.current_app.log_exception((exc_type, exc_value, tb))
        else:
            flask.flash(
                'Successfully changed tarif %s to %s.' % response.items()[0],
                'success')
            return flask.redirect(flask.url_for('.index'))
    return {'name': name, 'form': form}

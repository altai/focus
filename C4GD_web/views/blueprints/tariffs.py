"""List and update tariffs.

Restrict access of non-admin users.
"""
import sys

import flask
from flask import blueprints

from C4GD_web.models import abstract
from C4GD_web.views import environments
from C4GD_web.views import forms


bp = environments.admin(blueprints.Blueprint('tariffs', __name__))


@bp.route('')
def index():
    """List tariffs"""
    tariffs = abstract.Tariff.list()
    return {'tariffs': tariffs}


@bp.route('<path:name>/', methods=['GET', 'POST'])
def edit(name):
    """Edit tariff"""
    tariffs = abstract.Tariff.list()
    # TODO(apugachev) - handle nonexisting tariff, KeyError in next line
    form = forms.TariffEditForm(price=tariffs[name])
    if form.validate_on_submit():
        try:
            response = abstract.Tariff.update(
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

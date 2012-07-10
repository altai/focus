# -*- coding: utf-8 -*-

# Focus
# Copyright (C) 2010-2012 Grid Dynamics Consulting Services, Inc
# All Rights Reserved
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program. If not, see
# <http://www.gnu.org/licenses/>.


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

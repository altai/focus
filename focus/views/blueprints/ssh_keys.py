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


import re
import flask
from flask import blueprints
from flask import Response

from focus import clients
from focus.views import forms
from focus.views import environments

from openstackclient_base.exceptions import HttpException


bp = environments.project(blueprints.Blueprint('ssh_keys', __name__))


@bp.route('')
def index():
    c = clients.user_clients(flask.g.tenant_id)
    context = {
        'keys': c.nova.keypairs.list(),
        'delete_form': forms.DeleteForm(),
        'title': bp.name.replace('_', ' '),
        'subtitle': 'List of SSH keys'
    }
    return context


@bp.route('create/', methods=['GET', 'POST'])
def new():
    form = forms.CreateSSHKey()
    if form.validate_on_submit():
        create = clients.user_clients(flask.g.tenant_id).nova.keypairs.create
        try:
            if form.public_key.data:
                keypair = create(form.name.data, form.public_key.data)
            else:
                keypair = create(form.name.data)
        except HttpException as error:
            flask.flash(error.message, 'error')
            return {'form': form}
        if hasattr(keypair, 'private_key'):
            return Response(
                keypair.private_key,
                mimetype='application/binary',
                headers={'Content-Disposition': 'attachment; filename=%s.pem' %
                         re.sub('[^-a-zA-Z0-9]', '_', keypair.name)})
        flask.flash('Keypair was successfully created', 'success')
        return flask.redirect(flask.url_for('.index'))
    return {
        'form': form,
        'title': bp.name.replace('_', ' '),
        'subtitle': 'Add new SSH key'
    }


@bp.route('delete/<name>/', methods=['GET', 'POST'])
def delete(name):
    try:
        keypair = filter(
            lambda x: x.name == name,
            clients.user_clients(flask.g.tenant_id).nova.keypairs.list())[0]
    except IndexError:
        flask.abort(404)
    form = forms.DeleteForm()
    if form.validate_on_submit():
        keypair.delete()
        flask.flash('Keypair removed.', 'success')
        return flask.redirect(flask.url_for('.index'))
    return {
        'keypair': keypair,
        'form': form
    }

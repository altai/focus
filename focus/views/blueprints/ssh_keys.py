# coding=utf-8
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
        'delete_form': forms.DeleteForm()
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
    return {'form': form}


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

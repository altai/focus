# coding=utf-8
import novaclient

import flask
from flask import blueprints

from C4GD_web import clients
from C4GD_web import exceptions
from C4GD_web.views import forms
from C4GD_web.views import environments


bp = environments.project(blueprints.Blueprint('ssh_keys', __name__))


@bp.route('')
def index():
    c = clients.get_my_clients(flask.g.tenant_id)
    context = {
        'keys': c.nova.keypairs.list(),
        'delete_form': forms.DeleteForm()
        }
    return context


@bp.route('create/', methods=['GET', 'POST'])
def new():
    form = forms.CreateSSHKey()
    if form.validate_on_submit():
        c = clients.get_my_clients(flask.g.tenant_id).nova.keypairs.create
        if form.public_key.data:
            c(form.name.data, form.public_key.data)
        else:
            c(form.name.data)
        return flask.redirect(flask.url_for('.index'))
    return {'form': form}


@bp.route('delete/<name>/', methods=['GET', 'POST'])
def delete(name):
    try:
        keypair = filter(
            lambda x: x.name == name,
            clients.get_my_clients(flask.g.tenant_id).nova.keypairs.list())[0]
    except IndexError:
        abort(404)
    form = forms.DeleteForm()
    if form.validate_on_submit():
        keypair.delete()
        flask.flash('Keypair removed.', 'success')
        return flask.redirect(flask.url_for('.index'))
    return {
        'keypair': keypair,
        'form': form
        }

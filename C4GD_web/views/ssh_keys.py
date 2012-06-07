# coding=utf-

from flask import redirect, url_for, flash, abort
from flask import blueprints

from C4GD_web import exceptions
from C4GD_web.models import abstract
from C4GD_web.views import forms

bp = blueprints.Blueprint('ssh_keys', __name__, url_prefix='/ssh-keys')


@bp.route('/')
def index():
    context = {
        'keys': abstract.SSHKey.list(),
        'delete_form': forms.DeleteForm()
        }
    return context


@bp.route('/create/', methods=['GET', 'POST'])
def new():
    form = forms.CreateSSHKey()
    if form.validate_on_submit():
        try:
            keydata = abstract.SSHKey.create(**form.data)
        except exceptions.GentleException:
            name_exists = any([x for x in abstract.SSHKey.list() if x['name'] == form.data['name']])
            if name_exists:
                flash(
                    'Keypair with name %s already exists.' % form.data['name'],
                    'error')
            else:
                if form.data['public_key']:
                    flash('API was unable to register keypair.', 'error')
                else:
                    flash('API was unable to generate keypair.', 'error')
        else:
            if form.data['public_key']:
                flash('Keypair registered.', 'success')
            else:
                flash('Keypair generated and registered.', 'success')
                flash('Important! This is private key for generated keypair, copy it now, it won\'t be shown again! <br><code>%s</code>.' % keydata['private_key'], 'info')
            return redirect(url_for('.index'))
    return {
        'form': form
        }


@bp.route('/delete/<name>/', methods=['GET', 'POST'])
def delete(name):
    keydata = abstract.SSHKey.get(name)
    if keydata is None:
        abort(404)
    else:
        form = forms.DeleteForm()
        if form.validate_on_submit():
            abstract.SSHKey.delete(name)
            flash('Keypair removed.', 'success')
            return redirect(url_for('.index'))
        return {
            'keydata': keydata,
            'form': form
            }

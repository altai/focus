"""Project managent.

Currently project is a Keystone tenant + C-level network bound to the tenant.
Admins are allowed to create project, list them all, delete project.

TODO(apugachev) finish process of project deletion
"""
import sys

import flask
from flask import blueprints
from flaskext import principal

from C4GD_web import clients
from C4GD_web.views import forms
from C4GD_web.views import pagination


bp = blueprints.Blueprint('projects', __name__, url_prefix='/global/projects/')


@bp.before_request
def authorize():
    """Check user is authorized.

    Only admins are allowed here.
    """
    principal.Permission(('role', 'admin')).test()


@bp.route('')
def index():
    """List projects.

    List only enabled, sort by name.
    """

    tenants = clients.clients.keystone.tenants.list()
    ordered = sorted(tenants, key=lambda x: x.name)
    pagina = pagination.Pagination(ordered)
    delete_form = forms.DeleteForm()
    return {
        'objects': pagina.slice(ordered),
        'pagination': pagina,
        'delete_form': delete_form}


@bp.route('<object_id>', methods=['POST'])
def delete(object_id):
    """Deletes project.

    TODO(apugachev) remove VMs, images, network
    """
    try:
        tenant = clients.clients.keystone.tenants.get(object_id)
    except Exception, e:
        flask.flash('Can\'t get project with ID %s.' % e.args[0], 'error')
        exc_type, exc_value, tb = sys.exc_info()
        flask.current_app.log_exception((exc_type, exc_value, tb))
        return flask.redirect(flask.url_for('.index'))

    form = forms.DeleteForm()
    if form.validate_on_submit():
        try:
            tenant.delete()
        except Exception, e:
            flask.flash('Error occured: %s.' % e.args[0], 'error')
            exc_type, exc_value, tb = sys.exc_info()
            flask.current_app.log_exception((exc_type, exc_value, tb))
        else:
            flask.flash('Project removed successfully.', 'success')
    else:
        flask.flash('Form is not valid.', 'error')
    return flask.redirect(flask.url_for('.index'))


@bp.route('new/', methods=['GET', 'POST'])
def new():
    """Creates project.

    Currently network for the project is created automatically on first VM
    spawn. No sense to check network availability manually because on the
    moment of spawn network can be already used by some other project.
    Network can be taken by user of other tools.
    """
    form = forms.NewProject()
    if form.validate_on_submit():
        try:
            if form.description.data:
                clients.clients.keystone.tenants.create(
                    form.name.data, form.description.data)
            else:
                clients.clients.keystone.tenants.create(form.name.data)
        except Exception, e:
            flask.flash('Error occured: %s' % e.args[0], 'error')
            exc_type, exc_value, tb = sys.exc_info()
            flask.current_app.log_exception((exc_type, exc_value, tb))
        else:
            flask.flash('Project created.', 'success')
            return flask.redirect(flask.url_for('.index'))
    return {'form': form}


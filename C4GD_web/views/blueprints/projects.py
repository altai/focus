"""Project managent.

Currently project is a Keystone tenant + C-level network bound to the tenant.
Admins are allowed to create project, list them all, delete project.

TODO(apugachev) finish process of project deletion
"""
import flask
from flask import blueprints

from C4GD_web import clients
from C4GD_web import utils
from C4GD_web.models import orm
from C4GD_web.views import environments
from C4GD_web.views import forms
from C4GD_web.views import pagination


from openstackclient_base.exceptions import HttpException


bp = environments.admin(blueprints.Blueprint('projects', __name__))


@bp.route('')
def index():
    """List projects.

    List only enabled, sort by name.
    """

    tenants = utils.get_visible_tenants()
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

    TODO(apugachev) remove images
    """
    try:
        tenant = clients.admin_clients().keystone.tenants.get(object_id)
    except Exception:
        flask.abort(404)

    form = forms.DeleteForm()
    if form.validate_on_submit():
        try:
            # kill vms
            vms = filter(
                lambda x: x.tenant_id == object_id,
                clients.admin_clients().nova.servers.list(
                    search_opts={'all_tenants': 1}))
            for x in vms:
                x.delete()
            # detach network
            networks_client = clients.admin_clients().compute.networks
            networks = networks_client.list()
            for net in networks:
                if net.project_id == object_id:
                    networks_client.disassociate(net)
                    break
            # delete tenant
            tenant.delete()
            flask.flash('Project removed successfully.', 'success')
        except HttpException as ex:
            flask.flash('Cannot remote the project. %s' % ex.message, 'error')
    else:
        flask.flash('Form is not valid.', 'error')
    return flask.redirect(flask.url_for('.index'))


@bp.route('new/', methods=['GET', 'POST'])
def new():
    """Creates project.

    Bind network to the project at the same time.
    """
    form = forms.NewProject()
    admin_clients = clients.admin_clients()
    networks = admin_clients.compute.networks.list()
    form.network.choices = [
        (net.id, '%s (%s, %s)' % (net.label, net.cidr, net.vlan))
        for net in networks
        if net.project_id is None
    ]
    if form.validate_on_submit():
        if form.description.data:
            args = (form.name.data, form.description.data)
        else:
            args = (form.name.data, )
        tenant = admin_clients.keystone.tenants.create(*args)
        try:
            admin_clients.compute.networks.associate(
                form.network.data,
                tenant.id)
        except HttpException:
            tenant.delete()
            raise
        flask.flash('Project created.', 'success')
        return flask.redirect(flask.url_for('.index'))
    return {'form': form}

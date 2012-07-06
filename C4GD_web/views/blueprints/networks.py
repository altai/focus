import flask
from flask import blueprints

from C4GD_web import clients

from C4GD_web.views import environments
from C4GD_web.views import forms
from C4GD_web.views import pagination

from openstackclient_base.exceptions import HttpException


bp = environments.admin(blueprints.Blueprint('networks', __name__))


@bp.route('')
def index():
    networks = clients.admin_clients().compute.networks.list()
    tenants = clients.admin_clients().identity_admin.tenants.list()
    tenants = dict(((t.id, t.name) for t in tenants))
    p = pagination.Pagination(len(networks))
    offset = p.limit_offset()
    networks = [net._info for net in networks[offset[0]:offset[1]]]
    for net in networks:
        net["label"] = tenants.get(net["project_id"], net["label"])
    return {
        'objects': networks,
        'pagination': p,
        'delete_form': forms.DeleteForm()}


@bp.route('<object_id>/')
def show(object_id):
    net = clients.admin_clients().compute.networks.get(object_id)
    return {'object': dict(((k, '-' if v is None else v)
                            for k, v in net._info.iteritems()))}


@bp.route('new/', methods=['GET', 'POST'])
def new():
    """Create network.

    Insert record in db for network and create records for fixed IPs based on
    network CIDR.
    Creating fixed IPs like nova/network/manager.py:_create_fixed_ips()
    """
    form = forms.CreateNetwork()
    if form.validate_on_submit():
        label = 'net%s' % form.vlan.data
        try:
            networks = (clients.admin_clients().compute.networks.
                        create(label=label,
                               vlan_start=form.vlan.data,
                               cidr=form.cidr.data))
        except HttpException as ex:
            flask.flash(ex.message, 'error')
        else:
            flask.flash('Network %s created.' % label, 'success')
            return flask.redirect(flask.url_for('.index'))
    return {'form': form}


@bp.route('delete/<object_id>/', methods=['POST'])
def delete(object_id):
    """Delete network and associated fixed IPs."""
    form = forms.DeleteForm()
    if form.validate_on_submit():
        clients.admin_clients().compute.networks.delete(object_id)
        flask.flash('Network deleted.', 'success')
    return flask.redirect(flask.url_for('.index'))

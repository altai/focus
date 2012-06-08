# coding=utf-8
import functools

import flask
from flask import blueprints
from flaskext import principal

from storm.locals import *

from C4GD_web import benchmark
from C4GD_web import exceptions
from C4GD_web import utils
from C4GD_web.clients import clients, get_my_clients
from C4GD_web.models.abstract import VirtualMachine, Image, Flavor, KeyPair, SecurityGroup, SSHKey
from C4GD_web.views.utils import get_next_url
from C4GD_web.views.generic_billing import generic_billing
from C4GD_web.views import pagination
from C4GD_web.views import forms


bp = blueprints.Blueprint(
    'project_views', __name__, url_prefix='/projects/<tenant_id>');


@bp.url_value_preprocessor
def preprocess_tenant_id(endpoint, values):
    flask.g.tenant_id = values.pop('tenant_id')
    # don't do anything substantial in url preprocessor


@bp.before_request
def setup_tenant():
    principal.Permission(('role', 'member', flask.g.tenant_id)).test()
    flask.g.tenant_dict = flask.session['keystone_scoped']\
        [flask.g.tenant_id]['access']['token']['tenant']
    flask.g.c = get_my_clients(flask.g.tenant_id)
    flask.g.tenant = flask.g.c.keystone_service.tenants.get(flask.g.tenant_id)
    flask.g.project_managers = [user for user in flask.g.tenant.list_users() if any(
            filter(
                lambda role: role.name == 'projectmanager',
                user.list_roles(flask.g.tenant_id)))]


@bp.route('/')
def show_tenant():
    """
    List VMs for the project
    """
    vms_data = [x for x in VirtualMachine.list(tenant_id=flask.g.tenant_id) if \
                    x['tenant_id'] == flask.g.tenant_id]
    vms = enumerate(sorted(vms_data, key=lambda x: x['name']))
    p = pagination.Pagination(vms_data)
    return dict(vms=p.slice(vms_data), pagination=p)


@bp.route('/vms/spawn/', methods=['GET', 'POST'])
def spawn_vm():
    '''
    Spawn VM in the tenant.

    '''
    with benchmark.benchmark('Getting data via API'):
        images = Image.list()
        flavors = Flavor.list()
        security_groups = SecurityGroup.list()
        key_pairs = KeyPair.list()
    form = forms.get_spawn_form(images, flavors, security_groups, key_pairs)()
    if form.validate_on_submit():
        VirtualMachine.create(
            flask.g.tenant_id,
            form.name.data,
            form.image.data,
            form.flavor.data,
            form.password.data,
            form.keypair.data,
            form.security_groups.data)
        flask.flash('Virtual machine spawned.', 'success')
        return flask.redirect(flask.url_for(
                '.show_tenant', tenant_id=flask.g.tenant_id))
    return dict(form=form, tenant=flask.g.tenant)


@bp.route('/vms/<vm_id>/')
def show_vm(vm_id):
    server = clients.nova.servers.get(vm_id)
    try:
        flavor = clients.nova.flavors.get(server.flavor['id'])
    except Exception, e:
        # TODO(apugachev) look for NotFound exception from nova
        flavor = None
    try:
        image = clients.nova.images.get(server.image['id'])
    except Exception, e:
        # TODO(apugachev) look for NotFound exception from nova
        image = None
    return {
        'server': server,
        'flavor': flavor,
        'image': image}


@bp.route('/vms/<vm_id>/remove/', methods=['POST'])
def remove_vm(vm_id):
    '''
    Delete VM.
    No checks because currently OpenStack performs authorization checks.
    '''
    VirtualMachine.delete(vm_id, flask.g.tenant_id)
    flask.flash('Virtual machine removed successfully.', 'success')
    return flask.redirect(get_next_url())


@bp.route('/vms/<vm_id>/reboot/<type>/', methods=['POST'])
def reboot_vm(vm_id, type):
    """
    Reboot VM
    """
    VirtualMachine.reboot(flask.g.tenant_id, vm_id, type)
    flask.flash('Virtual machine rebooted successfully.', 'success')
    return flask.redirect(get_next_url())
    

@bp.route('/billing/')
def billing():
    return generic_billing(flask.g.tenant, flask.g.user)

    
@bp.route('/users/')
def list_users():
    """
    List users.
    """
    users = flask.g.tenant.list_users()
    p = pagination.Pagination(users)
    return {
        'pagination': p,
        'objects': p.slice(users)
        }

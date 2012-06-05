# coding=utf-8
import functools

import flask
from flask import blueprints

from C4GD_web import exceptions
from C4GD_web import utils
import forms

from storm.locals import *

from C4GD_web import benchmark
from C4GD_web.clients import clients
from C4GD_web.models.abstract import VirtualMachine, Image, Flavor, KeyPair, SecurityGroup, SSHKey


from .generic_billing import generic_billing
from .pagination import Pagination, per_page


from .utils import get_next_url


bp = blueprints.Blueprint(
    'project_views', __name__, url_prefix='/projects/<tenant_id>');


@bp.url_value_preprocessor
def preprocess_tenant_id(endpoint, values):
    tenant_id = values.pop('tenant_id')
    flask.g.tenant_id = tenant_id
    if 'keystone_scoped' in flask.session:
        try:
            tenant_dict = flask.session['keystone_scoped'][tenant_id]['access']['token']['tenant']
        except KeyError:
            utils.obtain_scoped(tenant_id)
            try:
                tenant_dict = flask.session['keystone_scoped'][tenant_id]['access']['token']['tenant']
            except KeyError:
                raise exceptions.GentleException('Tenant %s is not accessible for you.' % tenant_id)
        flask.g.tenant_dict = tenant_dict
    

@bp.before_request
def setup_tenant():
    flask.g.tenant = clients.keystone.tenants.get(flask.g.tenant_id)
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
    return dict(vms=vms)
 

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
    page = int(flask.request.args.get('page', 1))
    pagination = Pagination(page, per_page(), len(users))
    return {
        'pagination': pagination,
        'objects': users[(page-1) * per_page():per_page()]
        }

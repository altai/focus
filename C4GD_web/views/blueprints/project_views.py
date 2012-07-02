# coding=utf-8
import json
import re

import flask
from flask import blueprints

from C4GD_web import clients
from C4GD_web.models import abstract
from C4GD_web.views import forms
from C4GD_web.views import generic_billing
from C4GD_web.views import pagination
from C4GD_web.views import utils as views_utils
from C4GD_web.views import environments
from C4GD_web.views.blueprints import images

bp = environments.project(blueprints.Blueprint('project_views', __name__))


@bp.route('')
def show_tenant():
    """
    List VMs for the project
    """
    c = clients.user_clients(flask.g.tenant_id)
    servers = c.compute.servers.list(detailed=True)
    vms_data = [s._info for s in servers]
    vms_data = sorted(vms_data, key=lambda x: x['name'])
    p = pagination.Pagination(vms_data)
    data = p.slice(vms_data)
    user_id2name = {}
    uuid_regex = re.compile(
        r'[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-[a-f0-9]{4}-?[a-f0-9]{12}')
    for x in data:
        user_id = x['user_id']
        try:
            x['user_id'] = user_id2name[user_id]
            pass
        except KeyError:
            if user_id.isdigit() or uuid_regex.match(user_id):
                try:
                    user = clients.admin_clients().keystone.users.get(user_id)
                    user_id2name[user_id] = user.name
                    x['user_id'] = user.name
                except:
                    pass
    return {
        'vms': data,
        'pagination': p
    }


@bp.route('vms/spawn/', methods=['GET', 'POST'])
def spawn_vm():
    '''
    Spawn VM in the tenant.

    '''
    c = clients.user_clients(flask.g.tenant_id)
    images_list = images.get_images_list()
    flavors = c.nova.flavors.list()
    security_groups = c.nova.security_groups.list()
    key_pairs = c.nova.keypairs.list()

    form = forms.get_spawn_form(
        images_list, flavors, security_groups, key_pairs)()
    if form.validate_on_submit():
        c.nova.servers.create(
            form.name.data,
            form.image.data,
            form.flavor.data,
            key_name=form.keypair.data,
            security_groups=form.security_groups.data)
        flask.flash('Virtual machine spawned.', 'success')
        return flask.redirect(flask.url_for(
            '.show_tenant', tenant_id=flask.g.tenant_id))
    return {
        'form': form,
        'tenant': flask.g.tenant,
        'images': json.dumps([x._info for x in images_list]),
        'flavors': json.dumps([x._info for x in flavors])
    }


@bp.route('vms/<vm_id>/')
def show_vm(vm_id):
    server = clients.admin_clients().nova.servers.get(vm_id)
    try:
        flavor = clients.admin_clients().nova.flavors.get(server.flavor['id'])
    except Exception:
        # TODO(apugachev) look for NotFound exception from nova
        flavor = None
    try:
        image = clients.admin_clients().nova.images.get(server.image['id'])
    except Exception:
        # TODO(apugachev) look for NotFound exception from nova
        image = None
    return {
        'server': server,
        'flavor': flavor,
        'image': image}


@bp.route('vms/<vm_id>/remove/', methods=['POST'])
def remove_vm(vm_id):
    '''
    Delete VM.
    No checks because currently OpenStack performs authorization checks.
    '''
    abstract.VirtualMachine.delete(vm_id, flask.g.tenant_id)
    flask.flash('Delete operation requested for VM.', 'success')
    # NOT(apugachev)openstack can be slow; make a note to reflect the fact
    # of removing the VM on the next step
    if 'removed_vms' not in flask.session:
        flask.session['removed_vms'] = []
    flask.session['removed_vms'].append(vm_id)
    return flask.redirect(views_utils.get_next_url())


@bp.route('vms/<vm_id>/reboot/<type>/', methods=['POST'])
def reboot_vm(vm_id, type):
    """
    Reboot VM
    """
    abstract.VirtualMachine.reboot(flask.g.tenant_id, vm_id, type)
    flask.flash('Virtual machine rebooted successfully.', 'success')
    return flask.redirect(views_utils.get_next_url())


@bp.route('billing/')
def billing():
    return generic_billing.generic_billing(flask.g.tenant, flask.g.user)


@bp.route('users/')
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


@bp.route('get-credentials/')
def get_credentials():
    if 'download' in flask.request.args:
        user = flask.session['keystone_unscoped']['access']['user']['username']
        tenant = clients.admin_clients().keystone.tenants.get(
            flask.g.tenant_id).name
        keystone_url = flask.current_app.config['KEYSTONE_CONF']['auth_uri']
        response = flask.make_response(
            flask.render_template(
                'project_views/get_credentials.txt',
                **{
                    'user': user,
                    'tenant': tenant,
                    'keystone_url': keystone_url}))
        response.headers['Content-Disposition'] = \
            'attachment; filename=nova-rc-%s' % tenant
        response.headers['Content-Type'] = 'text/plain'
        return response
    else:
        return {}

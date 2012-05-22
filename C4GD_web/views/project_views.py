# coding=utf-8
from functools import wraps

from flask import g, request, session, current_app
from flask import render_template, make_response, jsonify, flash, redirect, url_for, abort
from flask.blueprints import Blueprint

from storm.locals import *

from C4GD_web.benchmark import benchmark
from C4GD_web.exceptions import GentleException
from C4GD_web.models.abstract import VirtualMachine, Image, Flavor, KeyPair, \
    SecurityGroup
from C4GD_web.models.orm import get_store, Tenant, UserRole, User, Role
from C4GD_web.utils import nova_get, obtain_scoped

from .generic_billing import generic_billing
from .pagination import Pagination, per_page

from .forms import get_spawn_form, get_new_user_to_project_form
from .utils import get_next_url


def pm_only(view):
    @wraps(view)
    def decorated(*args, **kwargs):
        if g.user.is_project_manager(g.tenant):
            return view(*args, **kwargs)
        else:
            flash('The operation is not available to you.', 'error')
            return make_response(render_template('blank.haml'), 403)
    return decorated


bp = Blueprint('project_views', __name__, url_prefix='/<tenant_id>');



@bp.url_value_preprocessor
def preprocess_tenant_id(endpoint, values):
    tenant_id = values['tenant_id']
    if 'keystone_scoped' in session:
        try:
            tenant_dict = session['keystone_scoped'][tenant_id]['access']['token']['tenant']
        except KeyError:
            obtain_scoped(tenant_id)
            try:
                tenant_dict = session['keystone_scoped'][tenant_id]['access']['token']['tenant']
            except KeyError:
                raise GentleException('Tenant %s is not accessible for you.' % tenant_id)
        g.tenant_id = tenant_id
        g.tenant_dict = tenant_dict
    

@bp.before_request
def setup_tenant():
    try:
        tenant = g.store.get(Tenant, g.tenant_id)
    except TypeError:
        tenant = g.store.get(Tenant, int(g.tenant_id))
    g.tenant = tenant
    user_ids = tenant.user_roles.find(UserRole.role_id.is_in([1, 4])).values(UserRole.user_id)
    project_managers = list(g.store.find(User, User.id.is_in(user_ids)).order_by(User.name).values(User.name))
    g.project_managers = project_managers


@bp.context_processor
def common_data():
    return {
        'tenant': g.tenant_dict,
        'project_managers': g.project_managers
        }


@bp.route('/')
def show_tenant(tenant_id):
    """
    List VMs for the project
    """
    response_data = nova_get(tenant_id, '/servers/detail')
    vms_data = [x for x in response_data['servers'] if \
                    x['tenant_id'] == tenant_id]
    vms = enumerate(sorted(vms_data, key=lambda x: x['name']))
    return dict(vms=vms)
 

@bp.route('/vms/spawn/', methods=['GET', 'POST'])
def spawn_vm(tenant_id):
    '''
    Spawn VM in the tenant.

    '''
    with benchmark('Getting data via API'):
        images = Image.list()
        flavors = Flavor.list()
        security_groups = SecurityGroup.list()
        key_pairs = KeyPair.list()
    form = get_spawn_form(images, flavors, security_groups, key_pairs)()
    if form.validate_on_submit():
        VirtualMachine.create(
            tenant_id,
            form.name.data,
            form.image.data,
            form.flavor.data,
            form.password.data,
            form.keypair.data,
            form.security_groups.data)
        flash('Virtual machine spawned.', 'success')
        return redirect(url_for('.show_tenant', tenant_id=tenant_id))
    return dict(form=form, tenant=g.tenant)


@bp.route('/vms/<int:vm_id>/remove/', methods=['POST'])
def remove_vm(tenant_id, vm_id):
    '''
    Delete VM.
    No checks because currently OpenStack performs authrisation checks.
    '''
    VirtualMachine.delete(vm_id, tenant_id)
    flash('Virtual machine removed successfully.', 'success')
    return redirect(get_next_url())


@bp.route('/users/')
def list_users(tenant_id):
    """
    List users.
    """
    users = g.tenant.users.find().order_by(User.name).config(distinct=True)
    page = int(request.args.get('page', 1))
    pagination = Pagination(page, per_page(), users.count())
    objects = users.config
    return {
        'pagination': pagination,
        'objects': users.config(offset=(page-1) * per_page(), limit=per_page())
        }


#@bp.route('/users/new/', methods=['GET', 'POST'])
@pm_only
def new_user_to_project(tenant_id):
    """
    # TODO: access control via Principal
    """
    users = g.store.find(
        User,
        Not(User.id.is_in(
                g.tenant.users.find().config(distinct=True).values(User.id)
                ))).config(distinct=True).order_by('name')
    roles = g.store.find(Role).order_by('name')
    form = get_new_user_to_project_form(users, roles)()

    if form.validate_on_submit():
        user = g.store.get(User, form.user.data)
        roles = g.store.find(Role, Role.id.is_in(form.roles.data))
        writable_store = get_store('RW')
        for role in roles:
            user_role = UserRole()
            user_role.user_id = user.id
            user_role.role_id = role.id
            user_role.tenant_id = g.tenant.id
            writable_store.add(user_role)
        writable_store.commit()
        flash('User added successfully', 'success')
        return redirect(url_for('.list_users', tenant_id=tenant_id))
    return {'form': form}


@bp.route('/users/<int:user_id>/remove/', methods=['POST'])
@pm_only
def remove_user_from_project(tenant_id, user_id):
    """
    Remove user from the project. Don't remove user itself.

    TODO: access control via Principal
    """
    writable_store = get_store('RW')
    rs = writable_store.find(
        UserRole, tenant_id=int(tenant_id), user_id=user_id)
    for user_role in rs:
        writable_store.remove(user_role)
    writable_store.commit() 
    flash('User removed successfully', 'success')
    return redirect(url_for('.list_users', tenant_id=tenant_id))
    

@bp.route('/billing/')
def billing(tenant_id):
    return generic_billing(tenant_id)

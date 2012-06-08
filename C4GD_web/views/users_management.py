"""User management for administrators.

Admins can list users, delete user, grant or revoke admin permissions.
TODO(apugachev) Consider having admin role id in settigns as a constant.
TODO(apugachev) Look for a simpler way of deciding if user is admin.
TODO(apugachev) Add warnings for destroying operations.
TODO(apugachev) Add navigation inside this blueprint's pages.
"""

import urlparse

from flask import request, redirect, url_for, flash, current_app
from flask import blueprints
from flaskext import principal

from C4GD_web.clients import clients
from C4GD_web.views.forms import DeleteUserForm, AddUserToProject, \
    RemoveUserFromProject 
from C4GD_web.views import pagination


bp = blueprints.Blueprint(
    'global_user_management', __name__, url_prefix='/global/users')


@bp.before_request
def authorize():
    principal.Permission(('role', 'admin')).test()


def get_admin_role_id():
    """Return ID of Admin role.

    :raises: RuntimeError if Admin roles does not exist
    """
    for role in clients.keystone.roles.list():
        if role.name == current_app.config['ADMIN_ROLE_NAME']:
            return role.id
    else:
        raise RuntimeError, 'Admin role does not exist'

    
def get_member_role_id():
    """Return ID of Member role.

    :raises: RuntimeError if Member roles does not exist
    """
    for role in clients.keystone.roles.list():
        if role.name == 'Member':
            return role.id
    else:
        raise RuntimeError, 'Member role does not exist'


@bp.route('/', methods=['GET'])
def index():
    """List users.

    TODO(apugachev): find way to count users without fetching all users.
    This would allow to use marker and limit to fetch one page only.
    """
    page = int(request.args.get('page', 1))
    users = clients.keystone.users.list(limit=1000000)
    p = pagination.Pagination(users)
    data = p.slice(users)
    tenants = clients.keystone.tenants.list(limit=1000000)
    for user in data:
        form = DeleteUserForm()
        form.user_id.data = user.id
        user.delete_form = form
        for tenant in tenants:
            user.is_global_admin = any(
                [x.name == current_app.config['ADMIN_ROLE_NAME'] for x in user.list_roles(tenant)])
            break
    return dict(pagination=p, data=data)


@bp.route('/<user_id>/', methods=['GET'])
def show(user_id):
    '''Show user details.

    Name, username, email, roles in tenants.
    '''
    user = clients.keystone.users.get(user_id)
    user_roles = []
    all_tenants = clients.keystone.tenants.list(limit=1000000)
    for tenant in all_tenants:
        roles = user.list_roles(tenant)
        if len(roles):
            user_roles.append((tenant, roles))
    add_user_to_project = AddUserToProject()
    add_user_to_project.user.data = user_id
    remove_user_from_project = RemoveUserFromProject()
    remove_user_from_project.user.data = user_id
    user_projects = []
    users_projects_choices = []
    not_user_projects_choices = []
    for tenant, role in user_roles:
        users_projects_choices.append((tenant.id, tenant.name))
        user_projects.append(tenant.id)
    remove_user_from_project.project.choices = users_projects_choices
    for tenant in all_tenants:
        if not tenant.id in user_projects:
            not_user_projects_choices.append((tenant.id, tenant.name))
    add_user_to_project.project.choices = not_user_projects_choices
    return dict(user=user, 
                user_roles=user_roles,
                add_user_to_project_form=add_user_to_project,
                remove_user_from_project_form=remove_user_from_project)
    

@bp.route('/add_user_to_project/', methods=['POST'])
def add_user_to_project():
    """
    Giving a 'Member' role in given tenant
    """
    form = AddUserToProject()
    tenant = clients.keystone.tenants.get(form.project.data) 
    tenant.add_user(form.user.data, get_member_role_id())
    flash('User was added to project', 'success')
    return redirect(url_for('.show', user_id=form.user.data))


@bp.route('/remove_user_from_project/', methods=['POST'])
def remove_user_from_project():
    """
    Removes all user's roles for given tenant
    """
    form = RemoveUserFromProject()
    project = clients.keystone.tenants.get(form.project.data) 
    user = clients.keystone.users.get(form.user.data)
    user_roles_in_project = []
    all_tenants = clients.keystone.tenants.list(limit=1000000)
    for tenant in all_tenants:
        if tenant.id == project.id:
            roles = user.list_roles(tenant)
            if len(roles):
                [user_roles_in_project.append(r) for r in roles]
    for role in user_roles_in_project:
        project.remove_user(form.user.data, role.id)
    flash('User was removed from project', 'success')
    return redirect(url_for('.show', user_id=form.user.data))


@bp.route('/<user_id>/grant/Admin/', methods=['GET'])
def grant_admin(user_id):
    """Grant admin permission.

    Add admin role with in admin tenant (aka systenant).

    TODO(apugachev): convert to POST
    TODO(apugachev): add form to plug in the CSRF protection
    """
    clients.keystone.roles.add_user_role(
        user_id,
        get_admin_role_id(),
        current_app.config['KEYSTONE_CONF']['admin_tenant_id'])
    flash('Admin role granted', 'success')
    return redirect(url_for('.index'))


@bp.route('/<user_id>/remove/Admin/', methods=['GET'])
def revoke_admin(user_id):
    """Revoke admin permission.

    Remove admin role in admin tenant (aka systenant).

    TODO(apugachev): convert to POST
    TODO(apugachev): add form to plug in the CSRF protection
    """
    clients.keystone.roles.remove_user_role(
        user_id,
        get_admin_role_id(),
        current_app.config['KEYSTONE_CONF']['admin_tenant_id'])
    flash('Admin role removed', 'success')
    return redirect(url_for('.index'))


@bp.route('/delete/', methods=['POST'])
def delete():
    """Delete user.

    Removes user from Keystone database.

    TODO(apugachev): pass user_id in path, make form empty just for CSRF sake.
    This provides better tracking via HTTPD logs.
    """
    form = DeleteUserForm()
    if form.validate_on_submit():
        clients.keystone.users.delete(form.user_id.data)
        flash('User was deleted', 'success')
    else:
        flash('User was not deleted', 'error')
    return redirect(url_for('.index'))

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

from C4GD_web.clients import clients
from C4GD_web.views.forms import DeleteUserForm 
from C4GD_web.views.pagination import Pagination, per_page


bp = blueprints.Blueprint(
    'global_user_management', __name__, url_prefix='/global/users')


def get_admin_role_id():
    """Return ID of Admin role.

    :raises: RuntimeError if Admin roles does not exist
    """
    for role in clients.keystone.roles.list():
        if role.name == 'Admin':
            return role.id
    else:
        raise RuntimeError, 'Admin role does not exist'


@bp.route('/', methods=['GET'])
def index():
    """List users.

    TODO(apugachev): find way to count users without fetching all users.
    This would allow to use marker and limit to fetch one page only.
    """
    page = int(request.args.get('page', 1))
    users = clients.keystone.users.list(limit=1000000)
    pagination = Pagination(page, per_page(), len(users))
    data = users[(page-1)*per_page():page*per_page()]
    tenants = clients.keystone.tenants.list(limit=1000000)
    for user in data:
        form = DeleteUserForm()
        form.user_id.data = user.id
        user.delete_form = form
        for tenant in tenants:
            user.is_global_admin = any(
                [x.name == 'Admin' for x in user.list_roles(tenant)])
            break
    return dict(pagination=pagination, data=data)


@bp.route('/<user_id>/', methods=['GET'])
def show(user_id):
    '''Show user details.

    Name, username, email, roles in tenants.
    '''
    user = clients.keystone.users.get(user_id)
    user_roles = []
    for tenant in clients.keystone.tenants.list(limit=1000000):
        roles = user.list_roles(tenant)
        if len(roles):
            user_roles.append((tenant, roles))
    return dict(user=user, user_roles=user_roles)


@bp.route('/<user_id>/grant/Admin/', methods=['GET'])
def grant_admin(user_id):
    """Grant admin permission.

    Adds role with name 'Admin' in admin tenant (aka systenant).
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

    Remove role with name 'Admin' in admin tenant (aka systenant).
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

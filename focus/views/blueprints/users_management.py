"""User management for administrators.

Admins can list users, delete user, grant or revoke admin permissions.
TODO(apugachev) Look for a simpler way of deciding if user is admin.
TODO(apugachev) Add warnings for destroying operations.
TODO(apugachev) Add navigation inside this blueprint's pages.
"""
import flask
from flask import blueprints

from focus import clients
from focus import utils
from focus.views import environments
from focus.views import forms
from focus.views import pagination


bp = environments.admin(
    blueprints.Blueprint('global_user_management', __name__))


@bp.route('', methods=['GET'])
def index():
    """List users.

    TODO(apugachev): find way to count users without fetching all users.
    This would allow to use marker and limit to fetch one page only.
    """
    identity_admin = clients.admin_clients().identity_admin
    users = sorted(
        identity_admin.users.list(limit=1000000),
        key=lambda x: x.name)
    p = pagination.Pagination(users)
    data = p.slice(users)
    potential_admins = set([
        user.id
        for user in (identity_admin.users.list(clients.get_systenant_id()))])
    for user in data:
        # TODO(apugachev) modify to work with form.DeleteUser
        form = forms.DeleteUserForm()
        form.user_id.data = user.id
        user.delete_form = form
        if user.id in potential_admins:
            for role in (identity_admin.roles.
                         roles_for_user(user.id)):
                if clients.role_tenant_is_admin(role):
                    user.is_global_admin = True
                    break
    return {
        'pagination': p,
        'data': data
    }


# TODO: rewrite this function in a more efficient way
@bp.route('<user_id>/', methods=['GET'])
def show(user_id):
    '''Show user details.

    Name, username, email, roles in tenants.
    '''
    def is_non_admin(tenant):
        return tenant.id != \
            clients.get_systenant_id()
    user = clients.admin_clients().keystone.users.get(user_id)
    user_roles = filter(
        lambda x: is_non_admin(x[0]),
        utils.user_tenants_with_roles_list(user))
    add_user_to_project = forms.AddUserToProject()
    add_user_to_project.user.data = user_id
    remove_user_from_project = forms.RemoveUserFromProject()
    remove_user_from_project.user.data = user_id
    user_projects = []
    users_projects_choices = []
    not_user_projects_choices = []
    for tenant, role in user_roles:
        if is_non_admin(tenant):
            users_projects_choices.append((tenant.id, tenant.name))
            user_projects.append(tenant.id)
    remove_user_from_project.project.choices = users_projects_choices
    all_tenants = clients.admin_clients().keystone.tenants.list()
    for tenant in all_tenants:
        if not tenant.id in user_projects and is_non_admin(tenant):
            not_user_projects_choices.append((tenant.id, tenant.name))
    add_user_to_project.project.choices = not_user_projects_choices
    return {
        'user': user,
        'user_roles': user_roles,
        'add_user_to_project_form': add_user_to_project,
        'remove_user_from_project_form': remove_user_from_project}


@bp.route('add_user_to_project/', methods=['POST'])
def add_user_to_project():
    """
    Giving a 'Member' role in given tenant
    """
    form = forms.AddUserToProject()
    tenant = clients.admin_clients().keystone.tenants.get(form.project.data)
    tenant.add_user(form.user.data, clients.get_role_id("member"))
    flask.flash('User was added to project', 'success')
    return flask.redirect(flask.url_for('.show', user_id=form.user.data))


@bp.route('remove_user_from_project/', methods=['POST'])
def remove_user_from_project():
    """
    Removes all user's roles for given tenant
    """
    form = forms.RemoveUserFromProject()
    project = clients.admin_clients().keystone.tenants.get(form.project.data)
    user = clients.admin_clients().keystone.users.get(form.user.data)
    user_roles_in_project = []
    all_tenants = clients.admin_clients().keystone.tenants.list(limit=1000000)
    for tenant in all_tenants:
        if tenant.id == project.id:
            roles = user.list_roles(tenant)
            if len(roles):
                [user_roles_in_project.append(r) for r in roles]
    for role in user_roles_in_project:
        project.remove_user(form.user.data, role.id)
    flask.flash('User was removed from project', 'success')
    return flask.redirect(flask.url_for('.show', user_id=form.user.data))


@bp.route('<user_id>/grant/Admin/', methods=['GET'])
def grant_admin(user_id):
    """Grant admin permission.

    Add admin role with in admin tenant (aka systenant).

    TODO(apugachev): convert to POST
    TODO(apugachev): add form to plug in the CSRF protection
    """
    clients.admin_clients().keystone.roles.add_user_role(
        user_id,
        clients.get_role_id("member"),
        clients.get_systenant_id())
    flask.flash('Admin role granted', 'success')
    return flask.redirect(flask.url_for('.index'))


@bp.route('<user_id>/remove/Admin/', methods=['GET'])
def revoke_admin(user_id):
    """Revoke admin permission.

    Remove admin role in admin tenant (aka systenant).

    TODO(apugachev): convert to POST
    TODO(apugachev): add form to plug in the CSRF protection
    """
    clients.admin_clients().keystone.roles.remove_user_role(
        user_id,
        clients.get_role_id("admin"),
        clients.get_systenant_id())
    flask.flash('Admin role removed', 'success')
    return flask.redirect(flask.url_for('.index'))


@bp.route('delete/', methods=['POST'])
def delete():
    """Delete user.

    Removes user from Keystone database.

    TODO(apugachev): pass user_id in path, make form empty just for CSRF sake.
    This provides better tracking via HTTPD logs.
    """
    form = forms.DeleteUserForm()
    if form.validate_on_submit():
        keystone_user = clients.admin_clients().keystone.users.get(
            form.user_id.data)
        if keystone_user.email:
            odb_user = utils.neo4j_api_call('/users', {
                "email": keystone_user.email
            }, 'GET')[0]
        else:
            odb_user_list = utils.neo4j_api_call('/users', method='GET')
            odb_user = filter(
                lambda x: x.username == keystone_user.name,
                odb_user_list)
        utils.neo4j_api_call('/users/%s' % odb_user['id'], method='DELETE')
        keystone_user.delete()
        flask.flash('User was deleted.', 'success')
    else:
        flask.flash('User was not deleted', 'error')
    return flask.redirect(flask.url_for('.index'))

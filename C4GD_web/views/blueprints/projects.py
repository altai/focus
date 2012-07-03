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
        store = orm.get_store('NOVA_RW')
        # kill vms
        vms = filter(
            lambda x: x.tenant_id == object_id,
            clients.admin_clients().nova.servers.list(
                search_opts={'all_tenants': 1}))
        for x in vms:
            x.delete()
        # detach network
        rows = store.execute(
            'SELECT vlan FROM networks WHERE project_id = ?',
            (object_id,))
        vlan = rows.get_one()[0]
        store.execute(
            'UPDATE networks SET project_id = NULL, label = ? '
            'WHERE project_id = ?',
            ('net' + vlan, object_id,))
        store.commit()
        # delete tenant
        tenant.delete()
        flask.flash('Project removed successfully.', 'success')
    else:
        flask.flash('Form is not valid.', 'error')
    return flask.redirect(flask.url_for('.index'))


@bp.route('new/', methods=['GET', 'POST'])
def new():
    """Creates project.

    Bind network to the project at the same time.
    """
    store = orm.get_store('NOVA_RW')
    form = forms.NewProject()
    rows = store.execute(
        'SELECT id, label, cidr, vlan FROM networks '
        'WHERE project_id IS NULL').get_all()
    form.network.choices = map(
        lambda x: (str(x[0]), '%s (%s, %s)' % (x[1:4])),
        rows)
    if form.validate_on_submit():
        if form.description.data:
            args = (form.name.data, form.description.data)
        else:
            args = (form.name.data, )
        tenant = clients.admin_clients().keystone.tenants.create(*args)
        try:
            store.execute(
                'UPDATE networks SET project_id = ?, label = ? '
                'WHERE id = ? AND project_id IS NULL LIMIT 1',
                (tenant.id, tenant.name, form.network.data))
            store.commit()
        except Exception:
            tenant.delete()
            raise
        flask.flash('Project created.', 'success')
        return flask.redirect(flask.url_for('.index'))
    return {'form': form}

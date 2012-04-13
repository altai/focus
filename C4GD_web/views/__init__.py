import authentication

from flask import g, render_template, make_response, jsonify

from C4GD_web import app
from C4GD_web.models import *
from C4GD_web.decorators import login_required

from wrappers import ProjectWrapper, GlobalAdminWrapper

from flask import g, flash, request, redirect, url_for, \
    session, abort
from storm.exceptions import NotOneError

from C4GD_web import app

from C4GD_web.benchmark import benchmark

from forms import get_login_form, get_spawn_form
from C4GD_web.models import *
from utils import get_object_or_404, get_next_url
from C4GD_web import app
from C4GD_web.models import get_pool, Tenant, UserRole, VirtualMachine
from flask import g, flash, render_template, request, redirect, url_for, \
    session

from pagination import Pagination
from dataset import IntColumn, StrColumn, ColumnKeeper
from csv_staff import UnicodeWriter
from cStringIO import StringIO
from contextlib import closing
import xml.etree.cElementTree as ET


@app.route('/')
@login_required
def dashboard():
    total_users = g.store.find(User).count()
    total_projects = g.store.execute('select count(distinct(tenant_id)) from user_roles').get_one()[0]
    return render_template(
        'dashboard.haml',
        total_users=total_users, total_projects=total_projects)


project_wrapper = ProjectWrapper()
global_wrapper = GlobalAdminWrapper()



@app.route('/<int:tenant_id>/')
@project_wrapper()
def show_tenant(tenant_id):
    """
    List VMs for the project
    """
    vms = enumerate(
        sorted(
            g.pool(
                VirtualMachine.list,
                bypass=lambda d: int(d['tenant_id']) == g.tenant.id),
        key=lambda x: x.name), 1)
    return dict(tenant=g.tenant, vms=vms)


@app.route('/<int:tenant_id>/spawn_vm/', methods=['GET', 'POST'])
@project_wrapper()
def spawn_vm(tenant_id):
    with benchmark('Getting form'):
        form = get_spawn_form()()
    if form.validate_on_submit():
        try:
            vm = g.pool(VirtualMachine.spawn, request.form)
        except RestfulException, e:
            flash(e.message, 'error')
        else:
            flash('Virtual machine spawned.', 'success')
            return redirect(url_for('show_tenant', tenant_id=g.tenant.id))
    return dict(form=form, tenant=g.tenant)


@app.route('/<int:tenant_id>/<int:vm_id>/remove_vm/', methods=['POST'])
@project_wrapper()
def remove_vm(tenant_id, vm_id):
    if request.method == 'POST':
        try:
            g.pool(VirtualMachine.remove, g.vm.id)
        except RestfulException, e:
            flash(e.message, 'error')
        else:
            flash('Virtual machine removed successfully.', 'success')
        return redirect(get_next_url())
    return {vm: g.vm}# use partial to show the same message as in modal


@app.route('/g/', defaults=dict(page=1))
@app.route('/g/<int:page>/')
@global_wrapper()
def global_list_vms(page):
    PER_PAGE = 10
    default_columns = ['id', 'name']
    columns = ColumnKeeper({
        'id': IntColumn('id', 'ID'),
        'name': StrColumn('name', 'Name'),
        'user_id': StrColumn('user_id', 'User')
        }, default_columns)
    if 'columns' in request.args:
        columns.adjust(request.args.getlist('columns'))
    vms = g.pool(VirtualMachine.list)
    table_data = [[x(obj) for x in columns.selected] for obj in vms]
    if 'export' in request.args:
        if request.args['export'] == 'json':
            result = jsonify(
                {
                    'header': [(x.attr_name, x.verbose_name) for x in columns.selected],
                    'body': table_data
                })
            result.headers['Content-Disposition'] = 'attachment; filename=vms.json'
            result.headers['Content-Type'] = 'application/json'
        elif request.args['export'] == 'csv':
            with closing(StringIO()) as f:
                writer = UnicodeWriter(f)
                writer.writerow(["%s|%s" % (x.attr_name, x.verbose_name) for x in columns.selected])
                writer.writerows([[str(j) for j in i] for i in table_data])
                result = make_response(f.getvalue())
            result.headers['Content-Disposition'] = 'attachment; filename=vms.csv'
            result.headers['Content-Type'] = 'text/csv'
        elif request.args['export'] == 'xml':
            r = ET.Element('results')
            header = ET.SubElement(r, 'head')
            for x in columns.selected:
                ET.SubElement(header, 'name', {'attr_name': x.attr_name, 'verbose_name': x.verbose_name})
            body = ET.SubElement(r, 'body')
            for data in table_data:
                row = ET.SubElement(body, 'row')
                for i, x in enumerate(data):
                    ET.SubElement(
                        row,
                        columns.selected[i].attr_name,
                        {
                            'value': repr(x),
                            'type': type(x).__name__
                            #'picled': 
                            })
            with closing(StringIO()) as f:
                ET.ElementTree(r).write(f)
                result = make_response(f.getvalue())
            result.headers['Content-Disposition'] = 'attachment; filename=vms.xml'
            result.headers['Content-Type'] = 'text/xml'
        else:
            abort(404)
    else:
        p = Pagination(page, PER_PAGE, len(table_data))
        visible_data_base = (page - 1) * PER_PAGE
        visible_data = table_data[
            visible_data_base:visible_data_base + PER_PAGE]
        result = dict(
            pagination=p,
            columns=columns,
            data=visible_data)
    return result

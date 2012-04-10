from flask import g, flash, render_template, request, redirect, url_for, \
    session
from storm.exceptions import NotOneError

from C4GD_web import app

from benchmark import benchmark
from decorators import login_required
from forms import get_login_form, get_spawn_form
from models import *
from rest_pool import get_pool
from utils import get_object_or_404


@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = get_login_form()()
    if form.validate_on_submit():
        user = g.store.find(User, name=form.username.data).one()
        if user is None:
            flash('User `%s` is not registered.' % form.username.data, 'error')
        if not user.enabled:
            flash('User `%s` is not enabled.' % user.name, 'error')
        if not user.is_ldap_authenticated(form.password.data):
            flash('Wrong username/password.', 'error')
        g.user = user
        session['user_id'] = g.user.id
        flash('You were logged in successfully.', 'success')
        return redirect(form.next.data)
    return render_template('login.haml', form=form)


@app.route('/')
@login_required
def index():
    return render_template(
        'index.haml',
        user_roles=g.store.find(UserRole, user_id=g.user.id))


@app.route('/logout/')
def logout():
    session.pop('user_id', None)
    flash('You were logged out', 'success')
    return redirect(url_for(app.config['DEFAULT_NEXT_TO_LOGOUT_VIEW']))


@app.route('/tenants/<int:tenant_id>/')
def show_tenant(tenant_id):
    """
    TODO: reorganize into pluggable view
    TODO: control user has requested tenant
    Shows list of VM available on the tenant
    """
    tenant = g.store.find(Tenant, id=tenant_id, enabled=True).one()
    pool = get_pool(g.user, tenant)
    vms = enumerate(pool(VirtualMachine.list, bypass=lambda tenant_id: int(tenant_id) == tenant.id)) 
    return render_template('tenants/show.haml', tenant=tenant, vms=vms)


@app.route('/maslennikov-mode-on/')
def maslennikov_mode_on():
    """
    TODO: load this on debug mode only
    """
    session['stashed_user_id'] = session['user_id']
    session['user_id'] = g.store.find(User, name=u'dmaslennikov').one().id
    session['maslennikov_mode'] = True
    return redirect(url_for('index'))

@app.route('/maslennikov-mode-off/')
def maslennikov_mode_off():
    """
    TODO: load this on debug mode only
    """
    session['user_id'] = session['stashed_user_id']
    del(session['maslennikov_mode'])
    return redirect(url_for('index'))



@app.route('/tenants/<int:tenant_id>/spawn/', methods=['GET', 'POST'])
def spawn_vm(tenant_id):
    """
    TODO: contorl user has this tenant
    """
    with benchmark('Getting tenant'):
        tenant = get_object_or_404(Tenant, tenant_id)
    with benchmark('Getting pool'):
        g.pool = get_pool(g.user, tenant)
    with benchmark('Getting form'):
        form = get_spawn_form()()
    if form.validate_on_submit():
        vm = g.pool(VirtualMachine.spawn, request.form)
        flash('Virtual machine spawned.', 'success')
        return redirect(url_for('show_tenant', tenant_id=tenant.id))
    with benchmark('Rendering page'):
        response = render_template('spawn_vm.haml', form=form, tenant=tenant)
    return response


@app.route('/tenants/<int:tenant_id>/vms/<int:vm_id>/')
def vm_details(vm_id):
    """
    TODO: control who can watch this
    """
    tenant = g.store.get(Tenant, tenant_id)
    # get vm from the tenant URL
    return render_template('vm_details.html')
        
        

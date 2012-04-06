from flask import g, flash, render_template, request, redirect, url_for, session
from storm.exceptions import NotOneError

from C4GD_web import app

from decorators import *
from models import *
from utils import *

@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = get_login_form()()
    if form.validate_on_submit():
        if are_ldap_authenticated(form.username.data, form.password.data):
            try:
                g.user = g.store.find(
                    User,
                    name=form.username.data, enabled=True).one()
            except NotOneError:
                flash('No enabled user `%s` in Keystone database' % \
                          form.username.data, 'error')
            else:
                session['user_id'] = g.user.id
                flash('You were logged in', 'success')
                return redirect(form.next.data)
        else:
            flash('Wrong username/password', 'error')
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
    vms = enumerate(get_vms_list_for_tenant(tenant))
    return render_template('tenants/show.haml', tenant=tenant, vms=vms)


@app.route('/maslennikov-mode-on/')
def maslennikov_mode_on():
    session['stashed_user_id'] = session['user_id']
    session['user_id'] = g.store.find(User, name=u'dmaslennikov').one().id
    session['maslennikov_mode'] = True
    return redirect(url_for('index'))

@app.route('/maslennikov-mode-off/')
def maslennikov_mode_off():
    session['user_id'] = session['stashed_user_id']
    del(session['maslennikov_mode'])
    return redirect(url_for('index'))


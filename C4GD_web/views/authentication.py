# coding=utf-8
from C4GD_web import app
from forms import get_login_form
from flask import g, flash, render_template, request, redirect, url_for, \
    session
from C4GD_web.models import User, RestfulPool
from _mysql_exceptions import OperationalError
from C4GD_web.utils import keystone_get, keystone_post, obtain_scoped
from C4GD_web.models.exceptions import InconsistentDatabaseException


@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = get_login_form()()
    if form.validate_on_submit():
        try:
            user = g.store.find(User, name=form.username.data).one()
        except OperationalError, e:
            if e.args[0] == 1267:
                flash('Username `%s` produces MySQL error.' % form.username.data, 'error')
            else:
                flash('MySQL error %s.' % e.args[0], 'error')
        else:
            if user is None:
                flash('User `%s` is not registered.' % form.username.data, 'error')
            elif user.user_roles.count() == 0:
                flash('User `%s` does not have any role.' % user.name, 'error')
            elif not user.enabled:
                flash('User `%s` is not enabled.' % user.name, 'error')
            elif not RestfulPool.save_token(form.username.data, form.password.data):
                flash('Wrong username/password', 'error')
            else:
                flash('You were logged in successfully.', 'success')
                tenants = keystone_get('/tenants')
                session['tenants'] = tenants
                if 'keystone_scoped' not in session:
                    session['keystone_scoped'] = {}
                for tenant in tenants['tenants']['values']:
                    obtain_scoped(tenant['id'])
                return redirect(form.next.data)
    return render_template('login.haml', form=form)

@app.route('/logout/')
def logout():
    session.clear()
    flash('You were logged out', 'success')
    return redirect(url_for(app.config['DEFAULT_NEXT_TO_LOGOUT_VIEW']))


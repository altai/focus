# coding=utf-8
from C4GD_web import app
from forms import get_login_form
from flask import g, flash, render_template, request, redirect, url_for, \
    session
from C4GD_web.models import User, RestfulPool
from _mysql_exceptions import OperationalError


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
                raise
        else:
            if user is None:
                flash('User `%s` is not registered.' % form.username.data, 'error')
            elif user.user_roles.count() == 0:
                flash('User `%s` does not have any role.' % user.name, 'error')
            elif not user.enabled:
                flash('User `%s` is not enabled.' % user.name, 'error')
            elif not (
                user.is_ldap_authenticated(form.password.data)
                    or
                user.is_keystone_credentials_authenticated(form.password.data)):
                flash('Wrong username/password.', 'error')
            else:
                g.user = user
                session['user_id'] = g.user.id
                RestfulPool.save_token(form.username.data, form.password.data)
                flash('You were logged in successfully.', 'success')
                return redirect(form.next.data)
    return render_template('login.haml', form=form)

@app.route('/logout/')
def logout():
    session.pop('user_id', None)
    flash('You were logged out', 'success')
    return redirect(url_for(app.config['DEFAULT_NEXT_TO_LOGOUT_VIEW']))

@app.context_processor
def auth_processor():
    return {
        'user': getattr(g, 'user', None),
        'authenticated': hasattr(g, 'user')}

@app.route('/maslennikov-mode-on/')
def maslennikov_mode_on():
    """
    TODO: load this on debug mode only
    """
    session['stashed_user_id'] = session['user_id']
    session['user_id'] = g.store.find(User, name=u'dmaslennikov').one().id
    session['maslennikov_mode'] = True
    return redirect(url_for('dashboard'))

@app.route('/maslennikov-mode-off/')
def maslennikov_mode_off():
    """
    TODO: load this on debug mode only
    """
    session['user_id'] = session['stashed_user_id']
    del(session['maslennikov_mode'])
    return redirect(url_for('dashboard'))

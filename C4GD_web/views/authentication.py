# coding=utf-8
from flask import g, session, request, current_app
from flask import flash, redirect, url_for

from C4GD_web import app
from C4GD_web.utils import keystone_get, obtain_scoped, keystone_obtain_unscoped

from .forms import get_login_form


@app.route('/login/', methods=['GET', 'POST'])
def login():
    """
    Log user in.

    Openstack KEystone component is our prime authentication source.
    Currently on login we are trying to obtain an unscoped token.
    On success we store the response in session as "unscoped_token".
    This piece of data is our authentication marker.
    If this is missing the user is not authenticated anymore.

    As a shortcut to save further work we instantly ask for scoped tokens
    for every tenant the user belongs to. These data is not important,
    it can be re-queried at any given moment.
    """
    form = get_login_form()()
    if form.validate_on_submit():
        success, unscoped_token_data = keystone_obtain_unscoped(
            form.username.data, form.password.data)
        if success: 
            flash('You were logged in successfully.', 'success')
            session["keystone_unscoped"] = unscoped_token_data
            tenants = keystone_get('/tenants')
            session['tenants'] = tenants
            if 'keystone_scoped' not in session:
                session['keystone_scoped'] = {}
            # this is not obvious but useful here
            for tenant in tenants['tenants']['values']:
                obtain_scoped(tenant['id'])
            return redirect(form.next.data)
        else:
            flash('Wrong username/password', 'error')
    return {'form': form}


@app.route('/logout/')
def logout():
    """
    Log user out.

    Instead of removing authentication merker only clear whole session.
    """
    session.clear()
    flash('You were logged out', 'success')
    return redirect(url_for(current_app.config['DEFAULT_NEXT_TO_LOGOUT_VIEW']))

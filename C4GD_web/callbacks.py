# coding=utf-8
from flask import g, session, request, current_app
from flask import redirect, url_for

from C4GD_web import app

from .models.orm import User, get_store


@app.before_request
def create_storm_readonly_store():
    g.store = get_store('RO')


@app.after_request
def commit_storm_store(response):
    if hasattr(g, 'store'):
        g.store.commit()
    return response

@app.teardown_request
def commit_storm_store_optionally(exception):
    if hasattr(g, 'store'):
        g.store.commit()


@app.before_request
def authenticate():
    g.is_authenticated = 'keystone_unscoped' in session
    if not g.is_authenticated:
        if request.endpoint not in current_app.config['ANONYMOUS_ALLOWED']:
            return redirect(url_for('login'))


@app.before_request
def inject_user():
    g.is_global_admin = g.is_authenticated and any([x.get('name') == 'Admin' for x in session['keystone_unscoped']['access']['user']['roles']])
    if g.is_authenticated:
        g.user = g.store.get(
            User, int(session['keystone_unscoped']['access']['user']['id']))


@app.before_request
def mock_xhr():
    if 'is_xhr' in request.args:
        request.environ['HTTP_X_REQUESTED_WITH'] = 'xmlhttprequest'


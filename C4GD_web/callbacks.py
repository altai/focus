# coding=utf-8
from flask import g, session
from C4GD_web import app
from models import User, get_store


@app.before_request
def create_storm_readonly_store():
    g.store = get_store('RO')

@app.after_request
def commit_storm_store(response):
    g.store.commit()
    return response

@app.teardown_request
def commit_storm_store_optionally(exception):
    if hasattr(g, 'store'):
        g.store.commit()


@app.before_request
def is_authenticated():
    g.is_authenticated = 'keystone_unscoped' in session
    g.is_global_admin = g.is_authenticated and any([x.get('name') == 'Admin' for x in session['keystone_unscoped']['access']['user']['roles']])

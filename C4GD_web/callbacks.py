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
def load_authenticated_user():
    if 'user_id' in session:
        g.user = g.store.find(
            User, id=session['user_id'], enabled=True).one()

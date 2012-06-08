# coding=utf-8
import flask

from C4GD_web import app
from C4GD_web.models import orm


@app.before_request
def create_storm_readonly_store():
    if flask.request.endpoint != 'static':
        flask.g.store = orm.get_store('RO')


@app.after_request
def commit_storm_store(response):
    if flask.request.endpoint != 'static':
        if hasattr(flask.g, 'store'):
            flask.g.store.commit()
    return response


@app.teardown_request
def commit_storm_store_optionally(exception):
    if flask.request.endpoint != 'static':
        if hasattr(flask.g, 'store'):
            flask.g.store.commit()


@app.before_request
def authenticate():
    if flask.request.endpoint != 'static':
        flask.g.is_authenticated = 'user' in flask.session
        if flask.g.is_authenticated:
            flask.g.user = flask.session['keystone_unscoped']['access']['user']
        else:
            if flask.request.endpoint not in flask.current_app.config['ANONYMOUS_ALLOWED']:
                return flask.redirect(flask.url_for('login'))


@app.before_request
def mock_xhr():
    if flask.request.endpoint != 'static':
        if 'is_xhr' in flask.request.args:
            flask.request.environ['HTTP_X_REQUESTED_WITH'] = 'xmlhttprequest'

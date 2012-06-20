# coding=utf-8
# TODO(apugachev) to 'main' blueprint
import flask

import C4GD_web
from C4GD_web.models import orm


@C4GD_web.app.before_request
def create_storm_readonly_store():
    if flask.request.endpoint != 'static':
        flask.g.store = orm.get_store('RO')


@C4GD_web.app.after_request
def commit_storm_store(response):
    if flask.request.endpoint != 'static':
        if hasattr(flask.g, 'store'):
            flask.g.store.commit()
    return response


@C4GD_web.app.teardown_request
def commit_storm_store_optionally(exception):
    if flask.request.endpoint != 'static':
        if hasattr(flask.g, 'store'):
            flask.g.store.commit()


@C4GD_web.app.before_request
def authenticate():
    if flask.request.endpoint != 'static':
        flask.g.is_authenticated = 'user' in flask.session
        if flask.g.is_authenticated:
            flask.g.user = flask.session['keystone_unscoped']['access']['user']
        else:
            if flask.request.endpoint not in \
                    flask.current_app.config['ANONYMOUS_ALLOWED']:
                return flask.redirect(flask.url_for('login'))


@C4GD_web.app.before_request
def mock_xhr():
    if flask.request.endpoint != 'static':
        if 'is_xhr' in flask.request.args:
            flask.request.environ['HTTP_X_REQUESTED_WITH'] = 'xmlhttprequest'

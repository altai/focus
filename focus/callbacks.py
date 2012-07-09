# coding=utf-8
# TODO(apugachev) to 'main' blueprint
import flask

import focus
from focus.models import orm


@focus.app.before_request
def authenticate():
    if flask.request.endpoint != 'static':
        flask.g.is_authenticated = 'user' in flask.session
        if flask.g.is_authenticated:
            flask.g.user = flask.session['keystone_unscoped']['access']['user']
        else:
            if flask.request.endpoint not in \
                    flask.current_app.config['ANONYMOUS_ALLOWED']:
                return flask.redirect(flask.url_for('login'))


@focus.app.before_request
def mock_xhr():
    if flask.request.endpoint != 'static':
        if 'is_xhr' in flask.request.args:
            flask.request.environ['HTTP_X_REQUESTED_WITH'] = 'xmlhttprequest'

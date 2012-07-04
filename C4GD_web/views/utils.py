# coding=utf-8
import flask


def get_next_url():
    """Defines URI to redirect to after login.

    Next destination can be provided as:
    - element "next" of request.args(GET) or request.form(POST),
    - app config DEFAULT_NEXT_TO_LOGIN_VIEW.
    """
    if flask.request.method == 'POST':
        d = flask.request.form
    else:
        d = flask.request.args
    return d.get('next', flask.url_for(
        flask.current_app.config['DEFAULT_NEXT_TO_LOGIN_VIEW']))

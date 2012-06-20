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


def get_object_or_404(klass, object_id, store=None):
    """Find object or raise HTTP 404.

    It can work with Storm model and reference set as klass.
    """
    if type(klass).__name__ == 'PropertyPublisherMeta':
        # this is a model
        if store is None:
            store = flask.g.store
        obj = store.get(klass, object_id)
    else:
        # this is a reference set
        obj = klass.find(id=object_id).config(distinct=True).one()
    if obj is None:
        flask.abort(404)
    else:
        return obj

from C4GD_web import app
from flask import abort, g, request, url_for


def get_next_url():
    """
    Defines URI to redirect to after login.
    It is provided as element "next" of request.args(GET) or request.form(POST).
    If it is not we use endpoint name from  app config DEFAULT_NEXT_TO_LOGIN_VIEW.
    
    Context: view.
    """
    if request.method == 'POST':
        d = request.form
    else:
        d = request.args
    return d.get('next', url_for(app.config['DEFAULT_NEXT_TO_LOGIN_VIEW']))


def get_object_or_404(klass, object_id):
    obj = g.store.get(klass, object_id)
    if obj is None:
        abort(404)
    else:
        return obj

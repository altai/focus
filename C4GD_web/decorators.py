import functools
import urllib
from C4GD_web import app
from flask import g, request, url_for, redirect

__all__ = ['login_required']

def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if hasattr(g, 'user'):
            return view(*args, **kwargs)
        else:
            return redirect(
                '%s?%s' % (
                    url_for('login'),
                    urllib.urlencode(
                        {app.config['NEXT_TO_LOGIN_ARG']: request.path})))
    return wrapped

# coding=utf-8
import functools
import urllib
from C4GD_web import app
from flask import g, request, url_for, redirect, session, jsonify


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if g.is_authenticated:
            return view(*args, **kwargs)
        else:
            if request.is_xhr:
                return  jsonify({'status': 'error',
                                 'message': 'Session expired',
                                 'code': 1})
            else:
                return redirect(
                    '%s?%s' % (
                        url_for('login'),
                        urllib.urlencode(
                            {app.config['NEXT_TO_LOGIN_ARG']: request.path})))
    return wrapped


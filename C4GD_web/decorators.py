# coding=utf-8
import functools
import urllib
from flask import g, request, url_for, redirect, session, jsonify, current_app


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
                            {current_app.config['NEXT_TO_LOGIN_ARG']: request.path})))
    return wrapped


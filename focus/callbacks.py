# -*- coding: utf-8 -*-

# Focus
# Copyright (C) 2010-2012 Grid Dynamics Consulting Services, Inc
# All Rights Reserved
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program. If not, see
# <http://www.gnu.org/licenses/>.


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

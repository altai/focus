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

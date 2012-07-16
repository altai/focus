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


"""Setting error handlers."""
import socket
import sys

import flask

import focus
from openstackclient_base.exceptions import HttpException, Unauthorized


@focus.app.errorhandler(Unauthorized)
def keystone_expired(error):
    """Handles expired Keyston token.

    No choice other then log the user out.
    """
    flask.flash(error.message, 'error')
    exc_type, exc_value, traceback = sys.exc_info()
    flask.current_app.log_exception((exc_type, exc_value, traceback))
    return flask.redirect(flask.url_for('logout'))


if not focus.app.debug:
    @focus.app.errorhandler(Exception)
    def everything_exception(error):
        """Handle all exceptions.

        Handles exceptions not caught before.
        If http referrer exists and belongs to our domain redirect there.
        Otherwise renders tempalte "blank.haml".
        """
        message = getattr(
            error,
            'public_message',
            error.message or error.args[0])
        exc_type, exc_value, traceback = sys.exc_info()
        flask.current_app.log_exception((exc_type, exc_value, traceback))
        # referrer is None if header is missing
        if flask.request.is_xhr:
            return flask.jsonify({'status': 'error', 'message': message, 'code': -1})
        else:
            flask.flash(message, 'error')
            if (flask.request.referrer or '').startswith(flask.request.host_url):
                return flask.redirect(flask.request.referrer)
            return flask.render_template('blank.haml')

    @focus.app.errorhandler(HttpException)
    def handle_openstackclient_http_exceptions(error):
        """Handle HTTP client exceptions.

        These exceptions can have 2 args (message and description).
        """
        flask.flash(error.message, 'error')
        focus.app.logger(error.code)
        exc_type, exc_value, traceback = sys.exc_info()
        flask.current_app.log_exception((exc_type, exc_value, traceback))
        return flask.render_template('blank.haml')


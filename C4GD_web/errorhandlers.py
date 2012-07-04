"""Setting error handlers."""
import sys

import flask

import C4GD_web
from openstackclient_base.exceptions import HttpException, Unauthorized


@C4GD_web.app.errorhandler(Unauthorized)
def keystone_expired(error):
    """Handles expired Keyston token.

    No choice other then log the user out.
    """
    flask.flash(error.message, 'error')
    exc_type, exc_value, traceback = sys.exc_info()
    flask.current_app.log_exception((exc_type, exc_value, traceback))
    return flask.redirect(flask.url_for('logout'))


if not C4GD_web.app.debug:
    @C4GD_web.app.errorhandler(Exception)
    def everything_exception(error):
        """Handle all exceptions.

        Handles exceptions not caught before.
        If http referrer exists and belongs to our domain redirect there.
        Otherwise renders tempalte "blank.haml".
        """
        flask.flash(error.message or error.args[0], 'error')
        exc_type, exc_value, traceback = sys.exc_info()
        flask.current_app.log_exception((exc_type, exc_value, traceback))
        # referrer is None if header is missing
        if (flask.request.referrer or '').startswith(flask.request.host_url):
            return flask.redirect(flask.request.referrer)
        return flask.render_template('blank.haml')

    @C4GD_web.app.errorhandler(HttpException)
    def handle_openstackclient_http_exceptions(error):
        """Handle HTTP client exceptions.

        These exceptions can have 2 args (message and description).
        """
        flask.flash(error.message, 'error')
        C4GD_web.app.logger(error.code)
        exc_type, exc_value, traceback = sys.exc_info()
        flask.current_app.log_exception((exc_type, exc_value, traceback))
        return flask.render_template('blank.haml')

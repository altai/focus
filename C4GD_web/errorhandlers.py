"""Setting error handlers."""
import sys

import flask

from C4GD_web import app
from C4GD_web import exceptions


@app.errorhandler(exceptions.KeystoneExpiresException)
def keystone_expired(error):
    """Handles expired Keyston token.

    No choice other then log the user out.
    """
    flask.flash(error.message, 'error')
    exc_type, exc_value, traceback = sys.exc_info()
    flask.current_app.log_exception((exc_type, exc_value, traceback))
    return flask.redirect(flask.url_for('logout'))


@app.errorhandler(exceptions.GentleException)
def gentle_exception(error):
    """Handles exception raised oftenly during API calls with.
    
    Handles situation with AJAX queries and wraps error message properly.
    """
    flask.flash(error.args[0], 'error')
    exc_type, exc_value, traceback = sys.exc_info()
    flask.current_app.log_exception((exc_type, exc_value, traceback))
    flask.current_app.logger.error(error.args[1].status_code)
    flask.current_app.logger.error(error.args[1].content)
    if flask.request.is_xhr:
        return flask.jsonify({'status': 'error', 'message': error.args[0]})
    else:
        return flask.render_template('blank.haml')


if not app.debug:
    @app.errorhandler(Exception)
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

import sys
from flask import flash, render_template, session, redirect, url_for
from flask import request, jsonify

from C4GD_web import app

import exceptions


@app.errorhandler(exceptions.KeystoneExpiresException)
def keystone_expired(error):
    flash(error.message, 'error')
    exc_type, exc_value, tb = sys.exc_info()
    app.log_exception((exc_type, exc_value, tb))
    return redirect(url_for('logout'))

@app.errorhandler(exceptions.GentleException)
def gentle_exception(error):
    flash(error.args[0], 'error')
    exc_type, exc_value, tb = sys.exc_info()
    app.log_exception((exc_type, exc_value, tb))
    # TODO(apugachev): separate Exception type for nova
    app.logger.error(error.args[1].status_code)
    app.logger.error(error.args[1].content)
    if request.is_xhr:
        return jsonify({'status': 'error', 'message': error.args[0]})
    else:
        return render_template('blank.haml')

if not app.debug:
    @app.errorhandler(Exception)
    def everything_exception(error):
        flash(error.message or error.args[0], 'error')
        exc_type, exc_value, tb = sys.exc_info()
        app.log_exception((exc_type, exc_value, tb))
        return render_template('blank.haml')

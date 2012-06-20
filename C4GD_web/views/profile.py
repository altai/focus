# coding=utf-8
# TODO(apugachev) to 'main' blueprint
import flask

import C4GD_web


@C4GD_web.app.route('/profile/', methods=['GET'])
def profile():
    """
    TODO(apugachev) Add password change form here.
    """
    return flask.render_template("profile.haml")

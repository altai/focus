# coding=utf-8
# TODO(apugachev) to 'main' blueprint
import flask

import focus


@focus.app.route('/profile/', methods=['GET'])
def profile():
    """
    TODO(apugachev) Add password change form here.
    """
    return flask.render_template("profile.haml")

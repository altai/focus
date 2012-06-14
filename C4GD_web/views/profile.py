# coding=utf-8
from flask import render_template, session

from C4GD_web import app


@app.route('/profile/', methods=['GET'])
def profile():
    """
    TODO(apugachev) Add password change form here.
    """
    return render_template("profile.haml")

    

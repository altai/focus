# coding=utf-8
from flask import render_template, session

from C4GD_web import app


@app.route('/profile/', methods=['GET'])
def profile():
    """
    For now shows a user's auth token for console usage
    """
    return render_template("profile.haml", 
       token=session['keystone_unscoped']['access']['token']['id'])
    
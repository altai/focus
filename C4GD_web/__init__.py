# coding=utf-8
import sys
from gevent import monkey
monkey.patch_all()

from flask import Flask
from flask import flash, render_template, session, redirect, url_for

from werkzeug import ImmutableDict
from flask_memcache_session import Session
from werkzeug.contrib.cache import MemcachedCache


from .application import FatFlask
from .blueprints.show_one import get_one
from .models.abstract import Image, VirtualMachine
from .exceptions import KeystoneExpiresException, GentleException
from .views.project_views import bp as project_views_bp
from .views.global_views import bp as global_views_bp



app = FatFlask(__name__)

app.jinja_env.hamlish_mode = 'indented' # if you want to set hamlish settings

app.cache = MemcachedCache(
    ['127.0.0.1:11211'],
    default_timeout=300000,
    key_prefix='focus')
app.session_interface = Session()

# config app
app.config.from_object('C4GD_web.default_settings')
app.config.from_object('C4GD_web.local_settings')

if not app.debug:
    import logging, sys
    logging.basicConfig(stream=sys.stderr)

 # TODO: move to blueprint

@app.errorhandler(KeystoneExpiresException)
def keystone_expired(error):
    flash(error.message, 'error')
    exc_type, exc_value, tb = sys.exc_info()
    app.log_exception((exc_type, exc_value, tb))
    return redirect(url_for('logout'))

@app.errorhandler(GentleException)
def gentle_exception(error):
    flash(error.args[0], 'error')
    exc_type, exc_value, tb = sys.exc_info()
    app.log_exception((exc_type, exc_value, tb))
    # TODO: separate Exception type for nova
    app.logger.error(error.args[1].status_code)
    app.logger.error(error.args[1].content)
    return render_template('blank.haml')

if not app.debug:
    @app.errorhandler(Exception)
    def everything_exception(error):
        flash(error.message, 'error')
        exc_type, exc_value, tb = sys.exc_info()
        app.log_exception((exc_type, exc_value, tb))
        return render_template('blank.haml')
    

import C4GD_web.callbacks
import C4GD_web.context_processors

import C4GD_web.views.authentication
import C4GD_web.views.dashboard

app.register_blueprint(get_one('images'), url_prefix='/images/', model=Image)
app.register_blueprint(get_one('virtual_machines'), url_prefix='/virtual-machines/', model=VirtualMachine)
app.register_blueprint(project_views_bp)
app.register_blueprint(global_views_bp)



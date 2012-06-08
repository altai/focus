# coding=utf-8
import logging
import sys
from gevent import monkey; monkey.patch_all()

from flask import Flask
from flaskext import uploads
from flask_memcache_session import Session
from werkzeug import ImmutableDict
from werkzeug.contrib.cache import MemcachedCache
from flaskext.mail import Mail

import application

app = application.FatFlask(__name__)

# config app
app.config.from_object('C4GD_web.default_settings')

try:
    app.config.from_object('C4GD_web.local_settings')
except ImportError:
    pass
try:
    app.config.from_pyfile("/etc/focus/local_settings.py")
except IOError:
    pass

app.jinja_env.hamlish_mode = 'indented'
app.cache = MemcachedCache(
    ['127.0.0.1:11211'],
    default_timeout=300000,
    key_prefix='focus')
app.session_interface = Session()
if not app.debug:
    logging.basicConfig(stream=sys.stderr)
    
# SMTP
mail = Mail(app)

from models import abstract
from views import global_views
from views import images
from views import project_views
from views import show_one
from views import ssh_keys
from views import users_management
from views import tariffs
# blueprints started
SHOW_ONES = (
    ('images', '/images/', abstract.Image),
    ('virtual_machines', '/virtual-machines/', abstract.VirtualMachine),
    ('volumes', '/volumes/', abstract.Volume)
)
for name, url_prefix, model in SHOW_ONES:
    app.register_blueprint(
        show_one.get_one(name), url_prefix=url_prefix, model=model)

app.register_blueprint(project_views.bp)
app.register_blueprint(global_views.bp)
app.register_blueprint(ssh_keys.bp)
app.register_blueprint(images.get_bp('global_images'), url_prefix='/global/images/')
app.register_blueprint(users_management.bp)
app.register_blueprint(tariffs.bp)

#  it is not clear how to implement public/private images
#app.register_blueprint(images.get_one('project_images'), url_prefix='/<project_id>/images/')


class ResolvingUploadSet(uploads.UploadSet):
    '''Quick workaround for extensinless filenames.'''

    def resolve_conflict(self, target_folder, basename):
        try:
            return super(ResolvingUploadSet, self).resolve_conflict(
                target_folder, basename)
        except ValueError:
            import uuid
            return str(uuid.uuid4())


files_uploads = ResolvingUploadSet('files', uploads.ALL)
uploads.configure_uploads(app, [files_uploads])

# these import app
import errorhandlers
import callbacks
import context_processors
import views.authentication
import views.authorization
import views.dashboard
import views.profile
import views.template_filters
import C4GD_web.invitations
import views.keystone2ODB

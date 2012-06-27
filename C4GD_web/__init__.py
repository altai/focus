# coding=utf-8
from gevent import monkey
monkey.patch_all()

import logging
import os
import socket
import sys

from logging import handlers

from flaskext import uploads
from werkzeug.contrib import cache
from flaskext import mail as mail_module

from C4GD_web import application
from C4GD_web import flask_memcache_session

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

if app.config['KEYSTONECLIENT_DEBUG']:
    os.environ['KEYSTONECLIENT_DEBUG'] = '1'
app.jinja_env.hamlish_mode = 'indented'
app.cache = cache.MemcachedCache(
    [app.config['MEMCACHED_HOST']],
    default_timeout=300000,
    key_prefix='focus')
app.session_interface = flask_memcache_session.Session()

if not app.debug:
    if len(app.config['ADMINS']):
        mail_handler = handlers.SMTPHandler(
            app.config['MAIL_SERVER'],
            app.config['DEFAULT_MAIL_SENDER'][1] \
                if len(app.config['DEFAULT_MAIL_SENDER']) == 2 \
                else app.config['DEFAULT_MAIL_SENDER'],
            app.config['ADMINS'],
            'Focus At %s Failed' % socket.getfqdn())
        mail_handler.setFormatter(logging.Formatter('''
Message type:       %(levelname)s
Location:           %(pathname)s:%(lineno)d
Module:             %(module)s
Function:           %(funcName)s
Time:               %(asctime)s

Message:

%(message)s
'''))
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)
    rotating_file_handler = handlers.RotatingFileHandler(
        app.config['LOG_FILE'],
        maxBytes=app.config['LOG_MAX_SIZE'],
        backupCount=app.config['LOG_BACKUPS'])
    rotating_file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
    ))
    rotating_file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(rotating_file_handler)

# SMTP
mail = mail_module.Mail(app)

from C4GD_web.models import abstract
from C4GD_web.views.blueprints import global_views
from C4GD_web.views.blueprints import images
from C4GD_web.views.blueprints import project_views
from C4GD_web.views.blueprints import show_one
from C4GD_web.views.blueprints import ssh_keys
from C4GD_web.views.blueprints import users_management
from C4GD_web.views.blueprints import tariffs
from C4GD_web.views.blueprints import projects
from C4GD_web.views.blueprints import networks
from C4GD_web.views.blueprints import invitation_domains
from C4GD_web.views.blueprints import invitations

# blueprints started
SHOW_ONES = (
    ('images', '/images/', abstract.Image),
    ('virtual_machines', '/virtual-machines/', abstract.VirtualMachine),
    ('volumes', '/volumes/', abstract.Volume)
)
for name, url_prefix, model in SHOW_ONES:
    app.register_blueprint(
        show_one.get_one(name), url_prefix=url_prefix, model=model)

app.register_blueprint(images.ABP, url_prefix='/global/images/')
app.register_blueprint(images.PBP, url_prefix='/projects/<tenant_id>/images/')
app.register_blueprint(project_views.bp, url_prefix='/projects/<tenant_id>/')
app.register_blueprint(global_views.bp, url_prefix='/global/')
app.register_blueprint(
    ssh_keys.bp,
    url_prefix='/projects/<tenant_id>/keypairs/')
app.register_blueprint(users_management.bp, url_prefix='/global/users/')
app.register_blueprint(tariffs.bp, url_prefix='/global/tariffs/')
app.register_blueprint(projects.bp, url_prefix='/global/projects/')
app.register_blueprint(networks.bp, url_prefix='/global/networks/')
app.register_blueprint(invitation_domains.bp, url_prefix='/global/invites/')
app.register_blueprint(invitations.bp, url_prefix='/invite/')


class ResolvingUploadSet(uploads.UploadSet):
    '''Quick workaround for extensionless filenames.'''

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
import C4GD_web.errorhandlers
import C4GD_web.callbacks
import C4GD_web.context_processors
import C4GD_web.views.authentication
import C4GD_web.views.authorization
import C4GD_web.views.dashboard
import C4GD_web.views.profile
import C4GD_web.views.template_filters

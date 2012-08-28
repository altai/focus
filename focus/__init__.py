# -*- coding: utf-8 -*-

# Focus
# Copyright (C) 2010-2012 Grid Dynamics Consulting Services, Inc
# All Rights Reserved
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program. If not, see
# <http://www.gnu.org/licenses/>.


import logging
import os
import socket

from logging import handlers

from flaskext import uploads
from werkzeug.contrib import cache
from flaskext import mail as mail_module

from focus import application
from focus import flask_memcache_session


app = application.FatFlask(__name__)

# config app
app.config.from_object('focus.default_settings')

try:
    app.config.from_object('focus.local_settings')
except ImportError:
    pass
try:
    app.config.from_pyfile("/etc/focus/local_settings.py")
except IOError:
    pass

LOG = logging.getLogger()
LOG.setLevel(logging.DEBUG if app.debug else logging.WARNING)
if app.config.get('LOG_FILE', '') != '':
    rotating_file_handler = handlers.RotatingFileHandler(
        app.config['LOG_FILE'],
        maxBytes=app.config['LOG_MAX_BYTES'],
        backupCount=app.config['LOG_BACKUP_COUNT'])
    rotating_file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
            ))
    LOG.addHandler(rotating_file_handler)
if not app.debug and len(app.config['ADMINS']):
    mail_handler = handlers.SMTPHandler(
        app.config['MAIL_SERVER'],
        app.config['DEFAULT_MAIL_SENDER'][1]
        if len(app.config['DEFAULT_MAIL_SENDER']) == 2
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
    LOG.addHandler(mail_handler)

app.jinja_env.hamlish_mode = 'indented'

app.cache = cache.MemcachedCache(
    [app.config['MEMCACHED_HOST']],
    default_timeout=2 * 60 * 60,
    key_prefix='focus')

app.session_interface = flask_memcache_session.Session()


# SMTP
mail = mail_module.Mail(app)

from focus.views.blueprints import global_views
from focus.views.blueprints import images
from focus.views.blueprints import security_groups
from focus.views.blueprints import project_views
from focus.views.blueprints import ssh_keys
from focus.views.blueprints import users_management
from focus.views.blueprints import tariffs
from focus.views.blueprints import projects
from focus.views.blueprints import networks
from focus.views.blueprints import notifications
from focus.views.blueprints import invitation_domains
from focus.views.blueprints import invitations
from focus.views.blueprints import load_history


app.register_blueprint(images.ABP, url_prefix='/global/images/')
app.register_blueprint(images.PBP, url_prefix='/projects/<tenant_id>/images/')
app.register_blueprint(security_groups.PBP,
                       url_prefix='/projects/<tenant_id>/security_groups/')
app.register_blueprint(project_views.bp, url_prefix='/projects/<tenant_id>/')
app.register_blueprint(global_views.bp, url_prefix='/global/')
app.register_blueprint(
    ssh_keys.bp,
    url_prefix='/projects/<tenant_id>/keypairs/')
app.register_blueprint(users_management.bp, url_prefix='/global/users/')
app.register_blueprint(tariffs.bp, url_prefix='/global/tariffs/')
app.register_blueprint(projects.bp, url_prefix='/global/projects/')
app.register_blueprint(networks.bp, url_prefix='/global/networks/')
app.register_blueprint(notifications.bp, url_prefix='/global/notifications/')
app.register_blueprint(invitation_domains.bp, url_prefix='/global/invites/')
app.register_blueprint(invitations.bp, url_prefix='/invite/')
app.register_blueprint(load_history.bp, url_prefix='/global/load_history/')


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
import focus.errorhandlers
import focus.callbacks
import focus.context_processors
import focus.views.authentication
import focus.views.authorization
import focus.views.dashboard
import focus.views.profile
import focus.views.template_filters

from werkzeug.wsgi import DispatcherMiddleware
from focus.zabbix_proxy import app as zabbix_data_api

#the_app = DispatcherMiddleware(zabbix_data_api)

app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
        '/zabbix_proxy': zabbix_data_api.wsgi_app
        })

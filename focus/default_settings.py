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


SECRET_KEY = 'g.U(\x8cQ\xbc\xdb\\\xc3\x9a\xb2\xb6,\xec\xad(\xf8"2*\xef\x0bd'
# GET/POST field name to store next after login URL
NEXT_TO_LOGIN_ARG = 'next'
# no next? redirect to this view
DEFAULT_NEXT_TO_LOGIN_VIEW = 'dashboard'
DEFAULT_NEXT_TO_LOGOUT_VIEW = 'login'

MAIL_USE_SSL = False
MAIL_DEBUG = True
MAIL_FAIL_SILENTLY = False

TEMPLATE_EXTENSION = '.haml'

ANONYMOUS_ALLOWED = [
    'login',
    'logout',
    'static',
    'convert_keystone_2_odb',
    'password_recovery_request',
    'password_recovery_finish',
    'update_passwords_in_ODB',
    'invitations.finish',
    'project_images.progress'
]

VNC_CONSOLE_TYPE = 'novnc'
DEFAULT_APP_PORT = 8080
# for keystone/nova/glance client
KEYSTONE_CONF = {
    'username': 'admin',
    'password': 'admin',
    'auth_uri': 'http://:5000/v2.0',
    'tenant_name': 'systenant',
}
SYSTENANT_NAME = 'systenant'

MEMCACHED_HOST = '127.0.0.1:11211'
KEYSTONECLIENT_DEBUG = False
ADMINS = []
LOG_FILE = '/var/log/focus/focus-tor.log'
LOG_MAX_BYTES = 1024 * 1024 * 100
LOG_BACKUP_COUNT = 12
DEV_LOG_TO_FILE = False

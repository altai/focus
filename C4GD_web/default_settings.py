# coding=utf-8
# our system has 13, keystone db 14 => 1
RELATIVE_TO_API_HOURS_SHIFT = 0
SECRET_KEY = 'g.U(\x8cQ\xbc\xdb\\\xc3\x9a\xb2\xb6,\xec\xad(\xf8"2*\xef\x0bd'
# GET/POST field name to store next after login URL
NEXT_TO_LOGIN_ARG = 'next'
# no next? redirect to this view
DEFAULT_NEXT_TO_LOGIN_VIEW = 'dashboard'
DEFAULT_NEXT_TO_LOGOUT_VIEW = 'login'

MAIL_USE_SSL = False
MAIL_DEBUG = True

TEMPLATE_EXTENSION = '.haml'

ANONYMOUS_ALLOWED = [
    'login',
    'logout',
    'static',
    'convert_keystone_2_odb',
    'password_recovery_request',
    'password_recovery_finish',
    'update_passwords_in_ODB',
    'invitations.finish'
]

DEFAULT_APP_PORT = 8080
# for keystone/nova/glance client
KEYSTONE_CONF = {
    'username': 'admin',
    'password': 'admin',
    'auth_uri': 'http://:5000/v2.0',
    'tenant_name': 'systenant',
}
# id of systenant, as string
DEFAULT_TENANT_ID = '1'
ADMIN_ROLE_NAME = 'Admin'
MEMCACHED_HOST = '127.0.0.1:11211'
KEYSTONECLIENT_DEBUG = False
ADMINS = []
LOG_FILE = '/var/log/focus/focus-tor.log'
LOG_MAX_SIZE = 1024 * 1024 * 100
LOG_BACKUPS = 12

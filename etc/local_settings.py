# coding=utf-8
DEBUG = False

UPLOADS_DEFAULT_DEST = '/var/lib/focus/uploads/'

INVITATIONS_DATABASE_URI = ''

KEYSTONE_CONF = {
    'username': 'admin',
    'password': 'admin',
    'auth_uri': 'http://:5000/v2.0',
    'tenant_name': 'systenant',
}

MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USERNAME = 'guess-who@griddynamics.com'
MAIL_PASSWORD = ''
MAIL_USE_TLS = True
DEFAULT_MAIL_SENDER = ('RobotName', MAIL_USERNAME)

KEYSTONECLIENT_DEBUG = False
ADMINS = []
LOG_FILE = '/var/log/focus/focus-tor.log'
LDAP_INTEGRATION = False

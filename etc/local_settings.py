# coding=utf-8
DEBUG = False

UPLOADS_DEFAULT_DEST = '/var/tmp/focus-uploads/'

INVITATIONS_DATABASE_URI = ''
NEO4J_API_URL = ''
NOVA_RW_DATABASE_URI = ''

KEYSTONE_CONF = {
    'username': 'admin',
    'password': 'admin',
    'auth_uri': 'http://:5000/v2.0',
    'tenant_name': 'systenant',
}

MAIL_SERVER = ''
MAIL_PORT = 25
DEFAULT_MAIL_SENDER = ('RobotName', 'robot_email@fake.to')
KEYSTONECLIENT_DEBUG = False
ADMINS = []
LOG_FILE = '/var/log/focus/focus-tor.log'

# coding=utf-8
RELATIVE_TO_API_HOURS_SHIFT = 0
DEBUG = False

UPLOADS_DEFAULT_DEST = '/var/tmp/focus-uploads/'

RO_DATABASE_URI = ''
RW_DATABASE_URI = ''
INVITATIONS_DATABASE_URI = ''
NEO4J_API_URL = ''
NOVA_RO_DATABASE_URI = ''
NOVA_RW_DATABASE_URI = ''

KEYSTONE_CONF = {
    'auth_uri': 'http://localhost:5000/v2.0/',
    'admin_tenant_name': 'systenant',
    'admin_user': 'admin',
    'admin_password': '999888777666',
    'admin_tenant_id': '1'
}

DEFAULT_TENANT_ID = KEYSTONE_CONF['admin_tenant_id']

MAIL_SERVER = ''
MAIL_PORT = 25
DEFAULT_MAIL_SENDER = ('RobotName', 'robot_email@fake.to')
KEYSTONECLIENT_DEBUG = False
ADMINS = []
LOG_FILE = '/var/log/focus/focus-tor.log'

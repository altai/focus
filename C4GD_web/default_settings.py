# coding=utf-8
RELATIVE_TO_API_HOURS_SHIFT = 0 # our system has 13, keystone db 14 => 1
SECRET_KEY = 'g.U(\x8cQ\xbc\xdb\\\xc3\x9a\xb2\xb6,\xec\xad(\xf8"2*\xef\x0bd'
NEXT_TO_LOGIN_ARG = 'next' # GET/POST field name to store next after login URL
DEFAULT_NEXT_TO_LOGIN_VIEW = 'dashboard' # no next? redirect to this view
DEFAULT_NEXT_TO_LOGOUT_VIEW = 'dashboard'

BILLING_URL = 'http://172.30.0.3:8787/v2'
TEMPLATE_EXTENSION = '.haml'
# endpoints allowed for anonymous to visit
ANONYMOUS_ALLOWED = ['login', 'static']
#  for runserver and tornado app runner
DEFAULT_APP_PORT = 5000
# for keystone/nova/glance client
KEYSTONE_CONF = {
    'admin_user': 'admin',
    'admin_password': 'admin',
    'auth_uri': 'http://:5000/v2.0',
    'admin_tenant_name': 'systenant',
    'admin_tenant_id': '1'
}
# id of systenant, as string
DEFAULT_TENANT_ID = "1"

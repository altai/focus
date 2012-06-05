# coding=utf-8
RELATIVE_TO_API_HOURS_SHIFT = 0 # our system has 13, keystone db 14 => 1
SECRET_KEY = 'g.U(\x8cQ\xbc\xdb\\\xc3\x9a\xb2\xb6,\xec\xad(\xf8"2*\xef\x0bd'
NEXT_TO_LOGIN_ARG = 'next' # GET/POST field name to store next after login URL
DEFAULT_NEXT_TO_LOGIN_VIEW = 'dashboard' # no next? redirect to this view
DEFAULT_NEXT_TO_LOGOUT_VIEW = 'dashboard'
LDAP_URI = 'ldap://ns/' 
LDAP_BASEDN = 'ou=people,ou=griddynamics,dc=griddynamics,dc=net'
KEYSTONE_URL = 'http://172.18.41.1:5000/v2.0'
BILLING_URL = 'http://172.30.0.3:8787/v2'
DEV = False
TEMPLATE_EXTENSION = '.haml'
ANONYMOUS_ALLOWED = ['login', 'static']
DEFAULT_APP_PORT = 5000
DEFAULT_TENANT_ID = '6'


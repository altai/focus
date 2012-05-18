# coding=utf-8
RELATIVE_TO_API_HOURS_SHIFT = 0 # our system has 13, keystone db 14 => 1
SECRET_KEY = 'g.U(\x8cQ\xbc\xdb\\\xc3\x9a\xb2\xb6,\xec\xad(\xf8"2*\xef\x0bd'
NEXT_TO_LOGIN_ARG = 'next' # GET/POST field name to store next after login URL
DEFAULT_NEXT_TO_LOGIN_VIEW = 'dashboard' # no next? redirect to this view
DEFAULT_NEXT_TO_LOGOUT_VIEW = 'dashboard'
LDAP_URI = 'ldap://ns/' 
LDAP_BASEDN = 'ou=people,ou=griddynamics,dc=griddynamics,dc=net'
RO_DB_HOST = ''
RO_DB_PORT = 3306 # must be integer
RO_DB_USER = ''
RO_DB_PASS = ''
RO_DB_NAME = ''
RW_DB_HOST = ''
RW_DB_PORT = 3306 # must be integer
RW_DB_USER = ''
RW_DB_PASS = ''
RW_DB_NAME = ''
KEYSTONE_URL = 'http://172.18.41.1:5000/v2.0'
BILLING_URL = 'http://172.30.0.3:8787/v1'
DEV = False


MAIL_SERVER = 'mail.vm.griddynamics.net'
MAIL_PORT = 25
MAIL_USE_SSL = False
MAIL_DEBUG = True
MAIL_USERNAME = 'c4gd-focus-robot@griddynamics.com'
MAIL_PASSWORD = None
DEFAULT_MAIL_SENDER = 'Do Not Reply'

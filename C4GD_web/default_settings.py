RELATIVE_TO_API_HOURS_SHIFT = 0 # our system has 13, keystone db 14 => 1
SECRET_KEY = 'g.U(\x8cQ\xbc\xdb\\\xc3\x9a\xb2\xb6,\xec\xad(\xf8"2*\xef\x0bd'
NEXT_TO_LOGIN_ARG = 'next' # GET/POST field name to store next after login URL
DEFAULT_NEXT_TO_LOGIN_VIEW = 'dashboard' # no next? redirect to this view
DEFAULT_NEXT_TO_LOGOUT_VIEW = 'dashboard'
LDAP_URI = 'ldap://ns/' 
LDAP_BASEDN = 'ou=people,ou=griddynamics,dc=griddynamics,dc=net'
DB_HOST = ''
DB_PORT = 3306 # must be integer
DB_USER = ''
DB_PASS = ''
DB_NAME = ''
DEV = False

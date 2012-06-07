# coding=utf-8
RELATIVE_TO_API_HOURS_SHIFT = 0
DEBUG = True

DEFAULT_APP_PORT = 5050

UPLOADS_DEFAULT_DEST = "/var/tmp/focus-uploads/"

RO_DATABASE_URI = ""
RW_DATABASE_URI = ""

KEYSTONE_CONF = {
    "auth_uri": "http://localhost:5000/v2.0/",
    "admin_tenant_name": "systenant",
    "admin_user": "admin",
    "admin_password": "999888777666",
    "admin_tenant_id": "1"
}

DEFAULT_TENANT_ID = KEYSTONE_CONF["admin_tenant_id"]

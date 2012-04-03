from fabric.api import *

try:
    from local_fab_settings import *
except ImportError:
    pass

def test():
    local('python tests.py')

def dev():
    local('export TOOLZA_CONFIG=local_settings.py && python toolza.py')

def generate_dev_settings():
    local('''echo "DEBUG = True

DB_HOST = 'localhost'
DB_USER = 'nova'
DB_PASS = 'nova'
DB_NAME = 'keystone'" > local_settings.py''')

def up():
    local('git push origin master')

def stage():
    local(
        'sudo chroot %s ssh %s "cd C4GD-web; git pull; pip-python install -r requirements.pip"' % (
            NOVA_CHROOT_PATH,
            STAGING_IP))

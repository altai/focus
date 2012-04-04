from fabric.api import *

try:
    from local_fab_settings import *
except ImportError:
    pass

def test():
    local('python tests.py')

def dev_get_db():
    local('mysqldump -u web_ro -pweb_ro -h 172.30.0.1 --add-drop-table --skip-lock-tables keystone > Ignored/keystone.dump.sql')
    local('mysql -u nova -pnova keystone < Ignored/keystone.dump.sql')


def dev():
    local('export TOOLZA_CONFIG=local_settings.py && export PYTHONPATH=`pwd`:$PYTHONPATH && python C4GD_web/runserver.py')

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

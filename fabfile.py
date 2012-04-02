from fabric.api import *

env.hosts = ['root@127.0.0.1:2222'] # this host has nova client and creds

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

def test_remotely():
    # spawn a node
    spawned = run('nova boot --flavor 1 --image 9 --key_name my-gd-key toolza-test-remote-1', )
    
    # install mysql
    run()
    # feed a dump
    # install openldap
    # create record
    # spawn a node
    # create bare git repo
    # push changes
    # reset repo
    # prepare test settings
    # run tests
    run('echo "hello"')

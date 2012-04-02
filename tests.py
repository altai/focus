import os
import re
import unittest
import toolza

DEBUG = False
DB_HOST = 'localhost'
DB_USER = 'nova'
DB_PASS = 'nova'
DB_NAME = 'keystone'

USER = 'apugachev'
SECRET = 'zarevo41'
TOKEN = 'ebdabed0-6b1f-4b6f-a434-07496e47f987' # keystine dump, token fixed

class BaseSetupTestCase(unittest.TestCase):
    def setUp(self):
        # set up: 1) LDAP, 2) MySQL
        # pass correct config values to toolza.app.config before assignment
        toolza.app.config.from_object(__name__)
        toolza.app.config['TESTING'] = True
        self.app = toolza.app.test_client()


class ToolzaSimpleUnitTestCase(unittest.TestCase):
    def test_get_next_url(self):
        with toolza.app.test_request_context('/login/', query_string={'next': '/foobar/'}):
            assert toolza.get_next_url() == '/foobar/'
        with toolza.app.test_request_context('/login/', method='POST', data={'next': '/buzz/'}):
            assert toolza.get_next_url() == '/buzz/'
        with toolza.app.test_request_context('/login/'):
            assert toolza.get_next_url() == '/'
        
    def test_mapped_dict(self):
        d = dict(A=2, B=4, C=6)
        mapping = dict(a='A', c='C')
        m = toolza.mapped_dict(d, mapping)
        assert m['a'] == 2
        assert m['c'] == 6
        assert len(m) == len(mapping)


class ToolzaComplexUnitTestCase(BaseSetupTestCase):
    def test_obtain_token(self):
        with self.app:
            assert toolza.obtain_token('no_such_name') is None
            assert toolza.obtain_token(USER) is not None

    def test_are_ldap_authenticated(self):
         with self.app:# this must be tested in mocked environment for fake user
            assert toolza.are_ldap_authenticated(USER, 'zarevo41')


class ToolzaFunctionalTestCase(BaseSetupTestCase):
    def test_login_required(self):
        rv = self.app.get('/')
        assert rv.status_code == 302
        assert rv.location == 'http://localhost/login/?next=%2F'

    def no_login(self, username, password):
        return self.app.post('/login/', data=dict(
            username=username,
            password=password
        ))

    def login(self, username, password):
        rv = self.app.get('/login/')
        csrf_token = self.scrape_csrf_token(rv.data)
        return self.app.post('/login/', data=dict(
            username=username,
            password=password,
            csrf_token=csrf_token
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout/', follow_redirects=True)
    
    def scrape_csrf_token(self, data):
        return re.search(
            '<input id="csrf_token" name="csrf_token" type="hidden" value="([^"]+)">',
            data).group(1)
        
    def test_login_logout(self):
        rv = self.login('', 'somepass')
        assert 'This field is required' in rv.data
        rv = self.login('fdfdfdfdfd', '')
        assert 'This field is required' in rv.data
        rv = self.no_login('admin', 'default')
        assert 'CSRF token missing' in rv.data
        rv = self.login('admin', 'default')
        assert 'Wrong username/password' in rv.data
        rv = self.login(USER, SECRET)
        assert 'You were logged in' in rv.data
        rv = self.logout()
        assert 'You were logged out' in rv.data
        
    def test_token(self):
        rv = self.login(USER, SECRET)
        assert TOKEN in rv.data
        

if __name__ == '__main__':
    # setup mocked up environment:
    # - LDAP
    # - MySQL
    unittest.main()

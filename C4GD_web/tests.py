import os
import re
import unittest
from C4GD_web import app
from utils import get_next_url, are_ldap_authenticated


class BaseSetupTestCase(unittest.TestCase):
    def setUp(self):
        # set up: 1) LDAP, 2) MySQL
        # pass correct config values to toolza.app.config before assignment
        app.config.from_object('test_settings.py')
        app.config['TESTING'] = True
        self.app = app.test_client()


class ToolzaSimpleUnitTestCase(unittest.TestCase):
    def test_get_next_url(self):
        with app.test_request_context('/login/', query_string={'next': '/foobar/'}):
            assert get_next_url() == '/foobar/'
        with app.test_request_context('/login/', method='POST', data={'next': '/buzz/'}):
            assert get_next_url() == '/buzz/'
        with app.test_request_context('/login/'):
            assert get_next_url() == '/'
        
class ToolzaComplexUnitTestCase(BaseSetupTestCase):
    def test_are_ldap_authenticated(self):
         with self.app:# this must be tested in mocked environment for fake user
            assert are_ldap_authenticated(USER, SECRET)


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
        assert 'os-core [Member]' in rv.data
        

if __name__ == '__main__':
    unittest.main()

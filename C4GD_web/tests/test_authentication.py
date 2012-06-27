# coding=utf-8
import mock
import unittest

from C4GD_web.views.authentication import _login
from C4GD_web.utils import create_hashed_password


class AuthenticationTestCase(unittest.TestCase):

    def setUp(self):
        self.ODB_GET_USER_RESPONSE = [{
            u'username': u'testaccount',
            u'login': u'test',
            u'passwordHash': u'',
            u'id': 277,
            u'email': u'testaccount@griddynamics.com'
        }]

        self.KEYSTONE_OBTAIN_UNSCOPED_RESPONSE = (
            True,
            {
             u'access':
             {
              u'token':
              {
               u'expires': u'2013-06-28T08:56:10Z',
               u'id': u'd0e6b839b3ac49e09f1c5b7bbe47f7e1'
              },
              u'serviceCatalog': {},
              u'user':
                {
                 u'username': u'testaccount',
                 u'roles_links': [],
                 u'id': u'295',
                 u'roles': [],
                 u'name': u'testaccount'
                }
              }
            }
        )

    def test_login(self):
        with \
                mock.patch('C4GD_web.utils.neo4j_api_call')\
                as neo4j_api_call, \
                mock.patch('C4GD_web.utils.keystone_obtain_unscoped')\
                as keystone_obtain_unscoped, \
                mock.patch('flask.current_app') as current_app,\
                mock.patch('flask.g') as g,\
                mock.patch('C4GD_web.clients.clients') as clients, \
                mock.patch('flask.flash') as flash, \
                mock.patch('flaskext.principal.identity_changed')\
                as identity_changed, \
                mock.patch('flask.session') as session:
            current_app.config = {
                'KEYSTONE_CONF': {
                    'admin_tenant_id': '1'}}
            neo4j_api_call.return_value = self.ODB_GET_USER_RESPONSE
            keystone_obtain_unscoped.return_value = \
                self.KEYSTONE_OBTAIN_UNSCOPED_RESPONSE

            self.ODB_GET_USER_RESPONSE[0]['passwordHash'] = \
                create_hashed_password(u'correctpassword')
            self.assertEqual(False, _login('testaccount', u'wrongpassword'))
            self.assertEqual(True, _login('testaccount', u'correctpassword'))

            self.ODB_GET_USER_RESPONSE[0]['passwordHash'] = \
                create_hashed_password(u'хорошийпароль')
            self.assertEqual(True, _login('testaccount1', u'хорошийпароль'))


if __name__ == '__main__':
    unittest.main()

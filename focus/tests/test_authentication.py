# -*- coding: utf-8 -*-

# Focus
# Copyright (C) 2010-2012 Grid Dynamics Consulting Services, Inc
# All Rights Reserved
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program. If not, see
# <http://www.gnu.org/licenses/>.


import mock
import unittest

from focus.views.authentication import _login
from focus.utils import create_hashed_password


class AuthenticationTestCase(unittest.TestCase):
    def setUp(self):
        self.ODB_GET_USER_RESPONSE = [
            {
                u'username': u'testaccount',
                u'login': u'test',
                u'passwordHash': u'',
                u'id': 277,
                u'email': u'testaccount@griddynamics.com'
            }
        ]
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
                mock.patch('focus.utils.neo4j_api_call')\
                as neo4j_api_call, \
                mock.patch('flask.current_app') as current_app,\
                mock.patch('flask.g'),\
                mock.patch('focus.clients.admin_clients'), \
                mock.patch('flask.flash'), \
                mock.patch('flaskext.principal.identity_changed'), \
                mock.patch('flask.session'):
            current_app.config = {
                'KEYSTONE_CONF': {
                    'admin_tenant_id': '1'}}
            neo4j_api_call.return_value = self.ODB_GET_USER_RESPONSE

            self.ODB_GET_USER_RESPONSE[0]['passwordHash'] = \
                create_hashed_password(u'correctpassword')
            self.assertEqual(False, _login('testaccount', u'wrongpassword'))
            self.assertEqual(True, _login('testaccount', u'correctpassword'))

            self.ODB_GET_USER_RESPONSE[0]['passwordHash'] = \
                create_hashed_password(u'хорошийпароль')
            self.assertEqual(True, _login('testaccount1', u'хорошийпароль'))


if __name__ == '__main__':
    unittest.main()

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
import json

from focus.utils import create_hashed_password

from focus.views.blueprints.invitations import register_user


class InvitationsTests(unittest.TestCase):

    def test_russian_password(self):
        """
        Verifies if user can enter a russian, japan (unicode) password after
        registration
        """
        for p in [u'фыва', u'asdf', u'君が代は 千代に 八千代に 細石の 巖と態']:
            self.assertEquals(type(''), type(create_hashed_password(p)))

    def test_interrupted_registration_test(self):
        """
        User received a invitation link, went to the registration form,
        entered password,
        KEYSTONE is configured correctly, ODB is not.
        User clicks register and he gets registered in keystone, and failed to
        register in ODB
        Next attempt to register using that URL from email will cause problem
        because user with that username already exists in keystone.
        """
        with \
            mock.patch('focus.clients.admin_clients') as clients,\
            mock.patch('focus.utils.username_is_taken')\
                as username_is_taken,\
            mock.patch(
                'focus.views.blueprints.invitations._register_in_ODB')\
                as _register_in_ODB:
            user = json.loads("""{"user": {"name": "spugachev+61", "enabled":
                 true, "email": "spugachev+61@griddynamics.com", "password":
                  "$6$rounds=40000$1b7qabKW35/cE/iy$xD..ZBPQiSJ1/8XRSW8nA4fjWIh
                 jHx1QRXNfK9gS6MLmDFmEuHC2XAbyKGpMezOK13ICC80bDZabOc7Cdi5xV0",
                  "id": "673f7199fdaf4c71b4c44d7f21d954d7",
                  "tenantId": null}}""")
            clients().keystone.users.create.return_value = user
            clients().keystone.users.delete.return_value = 'deleted'
            username_is_taken.return_value = False
            _register_in_ODB.side_effect = Exception(
                'Registration was interrupted, please try again')
            try:
                register_user('spugachev+61', 'spugachev+61@griddynamics.com',
                              'my_password', 'user')
            except Exception, e:
                clients().keystone.users.delete.assert_called_once_with(user)


if __name__ == '__main__':
    unittest.main()

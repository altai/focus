# coding=utf-8
import mock
import unittest

from C4GD_web.utils import create_hashed_password


class InvitationsTests(unittest.TestCase):
 
    def test_russian_password(self):
        """
        Verifies if user can enter a russian, japan (unicode) password after 
        registration  
        """
        for p in [u'фыва', u'asdf', u'君が代は 千代に 八千代に 細石の 巖と態']:
            self.assertEquals(type(''), type(create_hashed_password(p)))
        
if __name__ == '__main__':
    unittest.main()
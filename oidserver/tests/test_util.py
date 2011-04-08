# -*- coding: utf-8 -*-
import unittest

from services.util import (extract_username)

class TestUtil(unittest.TestCase):

    def test_extract_username(self):
#        self.assertEquals(extract_username('username'), 'username')
#        self.assertEquals(extract_username('test@test.com'),
#                          'u2wqblarhim5su7pxemcbwdyryrghmuk')
        # test unicode/punycode (straight UTF8 and urlencoded)
        self.assertEquals(extract_username('Fran%c3%a7ios@valid.test'),
                    'ym3nccfhvptfrhn7nkhhyvzgf2yl7r5y') # proper character
        self.assertEquals(extract_username('Fran%df%bfios@valid.test'),
                    'gbejqe5rmzej6xu3lo3g7lk2ptvgxehm') # max valid utf-8 char
        self.assertRaises(UnicodeDecodeError, extract_username,
                    'bo%EF%bb@badcharacter.test')       # bad utf-8 char
        self.assertRaises(UnicodeError, extract_username,
                    'bo%ef%bb%bc@badbidiuser.test')     # invalid BIDI char


 
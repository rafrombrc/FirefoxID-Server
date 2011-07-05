# -*- coding: utf-8 -*-
# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is Firefox Identity Server.
#
# The Initial Developer of the Original Code is JR Conlin
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****
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


 

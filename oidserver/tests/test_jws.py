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
from oidserver.tests import FakeAuthTool
from oidserver.jws import (JWS)
from oidserver.wsgiapp import make_app
from webtest import TestApp
from M2Crypto import RSA

import cjson
import base64
import unittest

"""
    Test the API
"""


class TestJWS(unittest.TestCase):

    # Please use valid credentials and targets
    good_credentials = {'email': 'good@example.com',
                        'password': 'good'}

    default_params = {'sid': '123abc',
                       'output': 'json',
                       'audience': 'test.example.com'}

    user_info = {'uid': 'test_api_1',
                 'pemail': 'good@example.com',
                 'emails': {'good@example.com': {'state': 'verified'},
                            'test@example.org': {'state': 'pending'}}
                }

    config = {
            'oidstorage.backend': 'memory',
            'oid.host': 'http://localhost:80',
            'auth.backend': '%s.%s' % (FakeAuthTool.__module__,
                                      FakeAuthTool.__name__),
#            'oidstorage.backend': 'mongo',
#            'oid.host': 'http: //web4.svc.mtv1.mozilla.com'
             'oid.mail_host': 'localhost',
             'oid.from_address': 'test@example.org',
             'oid.reply_to': 'no-reply@example.net',
             'oid.admin_page': True,
             'test.nomail': True,
             'global.debug_page': '__debug__',
             'jws.rsa_key_path': 'oidserver/tests/keys/test_rsa'
            }

    payload = {'a':1, 'b':2}
    # TO GENERATE A PUBLIC KEY:
    test_rsa_public = None;

    fake_sbs = 'test_string'


    ## API Entry points:
    #  get_certificate x
    #  refresh_certificate x
    #  validate/....
    #
    ## Admin entry points
    #  verify_address
    #

    ## beaker is being stupid and overwriting session information
    beaker_is_being_stupid = True

    extra_environ = {'beaker.session': {'uid': 'test_api_1'}}
    session = {}

    def setUp(self, **kw):
        # use a default 'dummy' config file.
        self.app = TestApp(make_app(self.config))
        self.app.reset()
        self.jws = JWS(config = self.config)


    def test_sign_HS256(self):
        alg = 'HS256'
        header = self.jws.header(alg)
        sbs = "%s.%s" % (base64.urlsafe_b64encode(cjson.encode(header)),
                         self.fake_sbs)
        signed = self.jws._sign_HS(alg, header, sbs)
        (header_str, payload_str, sig_str) = signed.split('.')
        self.failUnless(self.jws._verify_HS(alg,
                base64.urlsafe_b64decode(header_str),
                "%s.%s" % (header_str, payload_str),
                sig_str))

    def test_sign_RS256(self):
        alg = 'RS256'
        #jku = URL to public keys.
        rsa = RSA.load_key(self.config.get('jws.rsa_key_path'))

        #testKey = {'e': int(rsa.e.encode('hex'), 16),
        #       'n': int(rsa.n.encode('hex'), 16)}
        testKey = {'e': rsa.e, 'n': rsa.n}
        ## Don't store the public key, Needs to be "fetched" from a known
        ## location
        header = self.jws.header(alg = alg)
        sbs = "%s.%s" % (base64.urlsafe_b64encode(cjson.encode(header)),
                         self.fake_sbs)
        signed = self.jws._sign_RS(alg, header, sbs)
        # trim off the fake "sbs"
        (sbs, sig_str) = signed.rsplit('.',1)
        self.failUnless(self.jws._verify_RS(alg, header,
                                               sbs,
                                               sig_str,
                                               testKey = testKey))

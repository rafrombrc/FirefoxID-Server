# -*- coding: utf-8 -*-
from oidserver import VERSION
from oidserver.tests import FakeAuthTool, FakeRequest
from oidserver.jws import (JWS,
                          JWSException,
                          create_rsa_jki_entry)
from oidserver.wsgiapp import make_app
from webtest import TestApp
from M2Crypto import RSA, BIO

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

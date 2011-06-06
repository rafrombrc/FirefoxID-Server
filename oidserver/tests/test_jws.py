# -*- coding: utf-8 -*-
from oidserver import VERSION
from oidserver.tests import FakeAuthTool, FakeRequest
from oidserver.jws import (JWS,
                          JWSException,
                          create_rsa_jki_entry)
from oidserver.wsgiapp import make_app
from webtest import TestApp


import json
import base64
import unittest

"""
    Test the API
"""


class TestJWS(unittest.TestCase):

    bad_credentials = {'email': 'bad@example.com',
                       'password': 'bad'}

    # Please use valid credentials and targets
    good_credentials = {'email': 'good@example.com',
                        'password': 'good',
                        'pubKey': json.dumps({'algorithm':'HS256',
                                              'keydata': 'J RANDOM KEY'})}

    default_params = {'sid': '123abc',
                       'output': 'json',
                       'audience': 'test.example.com'}

    user_info = {'uid': 'test_api_1',
                 'pemail': 'good@example.com',
                 'emails': {'good@example.com': {'state': 'verified'},
                            'test@example.org': {'state': 'pending'}}
                }

    payload = {'a':1, 'b':2}
    test_rsa_keys = {'public': 'eyJlIjogNjk2MDUyNzk5NzcxNTMxNDUzLCAibiI6IDY1' +
                     'Mzk3NTc1OTQ5Mzc1MTY0NzUzOTgxNjc0ODc2NTk3NDE3Mzg3OTc0ND' +
                     'MzMDY0MTg1ODEyODk5NzUyMzAyMjU1MDc5MjQ4MDk4NjI0ODAzNTk2' +
                     'NTE3MjA4MzI0Njg3NTMxNjA1NTYwMzg0OTU1Njc3ODQzNjg1MTc2Mz' +
                     'I0NTA4NDAxNjkwNzQyODczMjM5MzM1MzM4MTUzNzl9',
                    'private': 'eyJxIjogOTMyMjE1OTkzOTE1Mjk3NzMxMTc0Nzc1MjI3' +
                    'ODA1ODkzODMwMjU2Njk2MjA2MTMxMDg5ODUyNDQ2MTk4ODg4OTAxMzU' +
                    '5MDM5LCAicCI6IDcwMTUyODE0NzcyNzkzMTY4MDcwOTk2NDMyMDc0ND' +
                    'g1MDU1NzY4NTE4OTM1NDc5ODgyNTY0NjUxMjkzMzUxNzM2MDUxMjE4N' +
                    'TMwMDgxMjYwNjEsICJkIjogMjE3MDQzMTYyNzIzNjYxMDA1ODIxNjI2' +
                    'NjQ5MDUyMjM2OTkyMDI5NjEzMDY3MjI2NjkyMDAxMzg1MDMwOTg5NjY' +
                    '4MjA4MjY1NTU2NTI3NTU1MTIwMDA1NDcwNTY0MzA2NTI1MDY3OTk0OT' +
                    'EzOTExMzc3NTkyNDk3MTYyMTkyMzk2NDgxMzY5MDk5NTI3MzE1MTIxO' +
                    'TYzMjU5N30='
                    }


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
             'jws.rsa_private_key': self.test_rsa_keys.get('private')
            }
        self.app = TestApp(make_app(config))
        self.app.reset()
        self.jws = JWS(config = config)


    def test_sign_HS256(self):
        signed = self.jws._sign_HS256({}, 'test_string')
        self.assertEqual(signed,
                         'Gc7RHDoAvOrksZ1FVD-jFgj9snfpjeDbxKOZcDt8p7A=')
        self.failUnless(self.jws._verify_HS256({}, 'test_string', signed))

    def test_sign_RS256(self):
        jki = []
        jki.append(create_rsa_jki_entry(self.test_rsa_keys.get('public')))
        #jku = URL to public keys.
        header = self.jws.header(jku = 'data:application/json;base64,' +
                  base64.b64encode(json.dumps({'keyvalues': jki})),
                  alg = 'RS256')
        import pdb; pdb.set_trace()
        signed = self.jws._sign_RS256(header, 'test_string')
        self.assertEqual(signed,
                         'MXB1eGxmLWJzQ0pLZnRPM2E3aGlGaTl2VzUzSVJsMXpjMDdXa' +
                         'FVZdmFTckxITHNSTU0xVjhqNGFQN0hHb3NlYjZmUEc1Y2llT0' +
                         'hpTmhWVGFvd0Q5c3o=')
        self.failUnless(self.jws._verify_RS256(header, 'test_string', signed))




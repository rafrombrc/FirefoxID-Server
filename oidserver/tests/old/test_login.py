# -*- coding: utf-8 -*-
import unittest
import urlparse
import json

from webtest import TestApp
from oidserver.wsgiapp import make_app
from services.auth.dummy import DummyAuth
from oidserver.tests import FakeAuthTool

"""
    Note: these tests do not validate installed configurations. To test live
    installations, be suer to pass the live configuration information to
    the make_app() call in TestLogin.setUp(), as well as call
    self.app.post('/login',credentials,status=expectedStatusCode) in the tests
"""

class TestLogin(unittest.TestCase):

    bad_credentials = {'email': 'bad@example.com',
                       'password': 'bad'}

    # Please use valid credentials and targets
    good_credentials = {'email': 'good@example.com',
                        'password': 'good'}

    def setUp(self):
        # use a default 'dummy' config file.
        config = {'auth.backend': '%s.%s' % (FakeAuthTool.__module__,
                                             FakeAuthTool.__name__),
            'oidstorage.backend': 'memory',
            'oid.host': 'http://localhost',
            'oid.assoc_expires_in': 3600}
        self.app = TestApp(make_app(config))


    def test_bad_login(self):
        response = self.app.post('/1/login', params=self.bad_credentials)
        import pdb; pdb.set_trace()
        self.failIf('Login failed' not in
                    response.body)


    def test_login(self):
        params = self.good_credentials.copy()
        params['output']='json'
        res = self.app.post('/1/login', params, status=200)
        self.failIf(json.loads(res.body)['success'] != True)

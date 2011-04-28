# -*- coding: utf-8 -*-
from oidserver import VERSION
from oidserver.tests import FakeAuthTool, FakeRequest
from oidserver.wsgiapp import make_app
from webtest import TestApp

import json
import unittest

"""
    Test the API
"""


class TestApi(unittest.TestCase):

    bad_credentials = {'email': 'bad@example.com',
                       'password': 'bad'}

    # Please use valid credentials and targets
    good_credentials = {'email': 'good@example.com',
                        'password': 'good'}

    default_params = {'sid': '123abc',
                       'output': 'json',
                       'audience': 'test.example.com'}

    user_info = {'uid': 'test_api_1',
                 'pemail': 'good@example.com',
                 'emails': ['good@example.com',
                            'test@example.org']}


    ## beaker is being stupid and overwriting session information
    beaker_is_being_stupid = True

    extra_environ = {'beaker.session': {'uid': 'test_api_1'}}
    session = {}

    def setUp(self, **kw):
        # use a default 'dummy' config file.
        config = {
            'oidstorage.backend': 'memory',
            'oid.host': 'http://localhost:80',
            'oid.assoc_expires_in': 3600,
            'auth.backend': '%s.%s' % (FakeAuthTool.__module__,
                                      FakeAuthTool.__name__),
#            'oidstorage.backend': 'mongo',
#            'oid.host': 'http: //web4.svc.mtv1.mozilla.com'
             'oid.mail_host': 'localhost',
             'oid.from_address': 'test@example.org',
             'oid.reply_to': 'no-reply@example.net',
             'test.nomail': True
            }
        self.app = TestApp(make_app(config))
        self.app.reset()
        self.prep_db(**kw)

    def check_default(self, result_obj, operation = None):
        """ Check that the default parameters survived """

        sid = result_obj.get('sid', None)
        self.failIf(sid is None)
        self.failIf(sid != self.default_params.get('sid', ''))
        if operation is not None:
            operation = operation[operation.rfind('/') + 1: ]
            roper = result_obj.get('operation', None)
            self.failIf(roper is None)
            self.assertEqual(roper, operation)

    def prep_db(self, set_assoc = True, **kw):
        """ """
        app = self.app.app.wrap_app.app

        request = FakeRequest()
#        if app.config['oidstorage.backend'] == 'memory':
        params = self.default_params.copy()
        params.update(self.good_credentials)
        request.params.update(params)
        if True:
            app.storage.create_user(self.user_info.get('uid'),
                                  pemail = self.user_info.get('pemail'),
                                  emails = self.user_info.get('emails'))
            # Log in the user.
            if (self.beaker_is_being_stupid):
                # beaker is overwriting extra_environ, so force the session
                # uid. This is an annoying hack around an annoying problem.
                app.controllers['auth'].fake_session['uid'] = \
                    self.user_info.get('uid')
            if set_assoc:
                app.storage.set_association(self.user_info.get('uid'),
                                    request,
                                    email = self.user_info.get('pemail'))
                self.app.post('/%s/login' % VERSION,
                                 params = params)

    def purge_db(self):
        storage = self.app.app.wrap_app.app.storage
        handle = storage.get_assoc_handle(uid = self.user_info.get('uid'),
                            request = None,
                            site_loc = self.default_params['audience'])
        storage.del_association(handle)
        storage.del_user(self.user_info.get('uid'), confirmed = True)

    def test_get_default_email(self):
        """ get the default email for this user """
        self.setUp()
        path = '/%s/get_default_email' % VERSION
        params = self.default_params.copy()
        response = self.app.post(path,
                                 params = params,
                                 extra_environ = self.extra_environ,
                                 status = 200)
        resp_obj = json.loads(response.body)
        self.check_default(resp_obj, path)
        self.failIf(resp_obj.get('email', '') !=
                    self.good_credentials.get('email'))
        self.purge_db()

    def test_get_emails(self):
        """ get list of valid emails for this user """
        self.setUp()
        path = '/%s/get_emails' % VERSION
        response = self.app.post(path,
                                 params = self.default_params,
                                 status = 200)
        resp_obj = json.loads(response.body)
        self.check_default(resp_obj, path)
        self.failIf('default' not in resp_obj)
        self.assertEqual(resp_obj.get('default'),
                         self.good_credentials.get('email'))
        self.failIf('emails' not in resp_obj)
        self.failIf(self.good_credentials.get('email')
                    not in resp_obj.get('emails'))
        self.purge_db()

    def test_get_identity_assertion(self):
        """ Get an identity assertion document for this user/site """
        self.setUp()
        path = '/%s/get_identity_assertion' % VERSION
        response = self.app.post(path,
                                 params = self.default_params,
                                 status = 200)
        resp_obj = json.loads(response.
                              body)
        self.check_default(resp_obj)
        self.failIf('iar' not in resp_obj)
        # verify the IAR

        params = self.default_params.copy()
        params.update({'iar': resp_obj.get('iar')})
        path = '/%s/verify' % VERSION
        response = self.app.post(path,
                      params = params,
                      status = 200)
        resp_obj = json.loads(response.body)
        self.check_default(resp_obj)
        self.failIf(resp_obj.get('success') != True)
        self.purge_db()

    def test_logged_in(self):
        """ check if the user is logged in to a given associated site """
        path = '/%s/logged_in' % VERSION
        self.app.reset()
        self.setUp()
        #"""
        # Test not logged in at all.
        # These tests are pending me figuring out how to kill sessions
        # in unit-test beaker.
        self.purge_db()
        params = self.default_params.copy()
        response = self.app.post(path,
                                 params = params,
                                 status = 200)
        json_obj = json.loads(response.body)
        self.failIf(json_obj['success'] != False or
                    json_obj['error']['code'] != 401)
        self.app.reset()
        # """
        #Test if the user is logged in, but no association exists.
        self.setUp(set_assoc = False)
        params = self.default_params.copy()
        response = self.app.post(path,
                                    params,
                                    extra_environ = self.extra_environ,
                                    status = 200)
        json_obj = json.loads(response.body)
        # Remember, user is logged in to identity, not the remote site.
        self.failIf(json_obj['success'] != False)
        # """
        #test if the user is logged in, with an active association
        self.purge_db()
        self.setUp()
        params = self.default_params.copy()
        params.update({'email': self.good_credentials.get('email')})
        self.app.reset()
        response = self.app.post(path,
                                 params = params,
                                 extra_environ = self.extra_environ,
                                 status = 200)
        json.loads(response.body)
        #test if the user is logged in with an invalid association
        self.app.app.wrap_app.app.storage.set_assoc_state(
            self.app.app.wrap_app.app.storage.get_assoc_handle(
                        self.user_info.get('uid'),
                        FakeRequest()),
            False)
        self.purge_db()

    def test_logout(self):
        self.setUp()
        path = "/%s/logout" % VERSION
        request = FakeRequest()
        request.remote_addr = "127.0.0.1"
        signature = self.app.app.wrap_app.app.\
                    controllers['auth'].gen_signature(
                        self.user_info.get('uid'),
                        request)
        params = self.default_params.copy()
        params.update({'sig': signature})

        self.app.post(path,
                    params = params,
                    extra_environ = self.extra_environ)
        storage = self.app.app.wrap_app.app.storage
        #cheating a bit since there should only be one association
        assoc = storage.get_associations_for_uid(self.user_info.get('uid'))[0]
        self.failIf(assoc['state'])

    def test_remove_association(self):
        """ Remove an association """
        self.setUp()
        params = self.default_params.copy()
        params.update({})
        path = '/%s/remove_association' % VERSION
        self.app.post(path, params = params, status = 200)
        self.purge_db()

    def test_bad_login(self):
        self.setUp()
        params = self.default_params.copy()
        params.update(self.bad_credentials)
        path = '/%s/login' % VERSION
        response = self.app.post(path, params = params)
        resp_obj = json.loads(response.body)
        self.check_default(resp_obj, path)
        self.failIf(resp_obj['error']['code'] != 401)

    def test_login(self):
        #page should return 302 (not 307)
        self.setUp()
        self.purge_db()
        params = self.default_params.copy()
        params.update(self.good_credentials)
        params.update({'output': 'html'})
        path = '/%s/login' % VERSION
        response = self.app.post(path,
                            params,
                            status = 200)
        ## This should return the assertion
        self.failIf('<meta name="page" content="terms" />' not in
                    response.body)
        params.update({'terms':'ok'})
        response = self.app.post(path, params = params, status = 200)
        self.failIf(self.user_info.get('pemail') not in response.body)

    def test_heartbeat(self):
        self.app.get('/__heartbeat__',
                     status = 200)

    def test_debug(self):
        resp = self.app.get('/__debug__',
                     status = 200)
        self.failIf('Debug information' not in resp.body)

    def test_update_info(self):
        self.setUp()
        storage = self.app.app.wrap_app.app.storage
        params = self.default_params.copy()
        test_info = {'name': "Leeroy Jenkins",
                     'data.avatar': "http://example.org/icon.jpg"}

        params.update(test_info)
        path = '/%s/manage_info' % VERSION
        self.app.post(path,
                      params = params,
                      extra_environ = self.extra_environ,
                      status = 302)
        user = storage.get_user_info(self.user_info.get('uid'))
        self.assertEqual(user.get('name', None), test_info.get('name'))
        self.assertEqual(user.get('data',{}).get('avatar', None),
                         test_info.get('data.avatar'))

        bad_info = {'name': '<script>alert("Evil");</script>',
                    'data.avatar': 'script:alert("Evil)'}
        params.update(bad_info)
        self.app.post(path,
                      params = params,
                      extra_environ = self.extra_environ,
                      status = 302)
        user = storage.get_user_info(self.user_info.get('uid'))
        self.failIf('<script>' in user.get('name'))
        self.failIf(user.get('data').get('avatar', ''))
        self.purge_db()

    def test_add_email(self):
        self.setUp()
        storage = self.app.app.wrap_app.app.storage
        params = self.default_params.copy()
        test_info = {'unv': 'supplemental@example.org', 'act': 'add'}

        params.update(test_info)
        path = '/%s/manage_email' % VERSION
        response = self.app.post(path,
                      params = params,
                      extra_environ = self.extra_environ,
                      status = 200
                      )
        user = storage.get_user_info(self.user_info.get('uid'))
        ## pull the confirmation code
        conf_code = \
            user.get('unv_emails').get(test_info['unv']).get('conf_code')

        params = self.default_params.copy()
        path = ('/%s/validate/' % VERSION) + conf_code
        response = self.app.get(path,
                                 params = params,
                                 extra_environ = self.extra_environ,
                                 status = 200)
        self.failIf('<meta name="page" content="conf_email" />' not in
            response.body)

        user = storage.get_user_info(self.user_info.get('uid'))
        self.failIf(test_info['unv'] not in user.get('emails'))
        if user['unv_emails']:
            self.failIf(test_info['unv'] in user['unv_emails'])

import unittest

from webtest import TestApp
from oidserver.wsgiapp import make_app
from oidserver.tests import test_config
from oidserver.tests import FakeRequest

MONGO = False
try:
    if test_config.get('oidstorage.backend','memory') == 'mongo':
        from oidserver.storage.mongo import MongoStorage # NOQA
        MONGO = True
except ImportError:
    pass

if MONGO:

    class TestMongo(unittest.TestCase):

        bad_credentials = {'email': 'bad@example.com',
                           'password': 'bad'}

        # Please use valid credentials and targets
        good_credentials = {'email': 'good@example.com',
                            'password': 'good'}

        default_params = {'sid': '123abc',
                          'output': 'json'}

        user_info = {'uid': 'test_mongo_1',
                     'pemail': 'good@example.com',
                     'emails': ['good@example.com',
                                'test@example.org']}

        extra_environ = {'beaker.session': {'logged_in': 'test_mongo_1'}}

        def setUp(self):
            config = {
                    'auth.backend': 'dummy',
                    'oidstorage.backend': 'mongo',
                    #oid.host': 'http://localhost',
                    'oidstorage.host': 'web4.dev.svc.mtv1.mozilla.com',
                    'oidstorage.port': 27017}

            user = test_config.get('auth.credentials').encode('base64')
            self.auth = {'HTTP_AUTHORIZATION': 'Basic ' + user}
            self.app = TestApp(make_app(config))

        # Create the user (used across the next few tests)
        def test_add_user(self):
            storage = self.app.app.wrap_app.app.storage
            uid = self.user_info.get('uid')
            user_info = storage.create_user(uid,
                        pemail = self.user_info.get('pemail'))
            f_user_info = storage.get_user_info(uid)
            self.assertEqual(user_info, f_user_info)
            request = FakeRequest()
            assoc = storage.set_association(uid, request)
            self.failIf(assoc == None)

        def test_associations(self):
            storage = self.app.app.wrap_app.app.storage
            request = FakeRequest()
            ## This should create the user
            uid = self.user_info.get('uid')
            handle = storage.get_assoc_handle(uid, request)
            assoc = storage.get_association(handle)
            u_associations = storage.get_associations_for_uid(uid)
            self.assertEqual(len(u_associations), 1)
            self.assertEqual(u_associations[0], assoc)
            e_associations = storage.get_associations_by_email(
                self.user_info.get('pemail'),
                handle)
            self.assertEqual(len(e_associations), 1)
            self.assertEqual(e_associations[0], assoc)
            emails = storage.get_emails(uid, handle)
            self.assertEqual(emails.get(u'default'),
                             self.user_info.get('pemail'), )
            storage.del_association(handle,
                                    self.user_info.get('pemail'))
            associations = storage.get_associations_for_uid(uid)
            self.assertEqual(len(associations), 0)

        # Delete the created user record.
        def test_user(self):
            storage = self.app.app.wrap_app.app.storage
            uid = self.user_info.get('uid')
            storage.del_user(uid, True)
            user = storage.get_user_info(uid)
            self.assertEqual(user, None)

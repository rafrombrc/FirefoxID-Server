import unittest

from webtest import TestApp
from oidserver.wsgiapp import make_app
from oidserver.tests import test_config
from oidserver.tests import FakeRequest

REDIS = False
try:
    if test_config.get('oidstorage.backend','memory') == 'redis':
        from oidserver.storage._redis import RedisStorage # NOQA
        REDIS = True
except ImportError:
    pass

if REDIS:

    class TestRedis(unittest.TestCase):

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
                    'oidstorage.backend': 'redis',
                    #oid.host': 'http://localhost',
                    'oidstorage.host': 'id1.dev.mtv1.svc.mozilla.com',
                    'oidstorage.port': 6379}

            user = test_config.get('auth.credentials').encode('base64')
            self.auth = {'HTTP_AUTHORIZATION': 'Basic ' + user}
            self.app = TestApp(make_app(config))

        # Create the user (used across the next few tests)
        def test_add_user(self):
            storage = self.app.app.wrap_app.app.storage
            uid = self.user_info.get('uid')
            user_info = storage.create_user(uid,
                        self.user_info.get('pemail'))
            self.assertNotEqual(user_info, None)
            f_user_info = storage.get_user_info(uid)
            self.assertEqual(user_info, f_user_info)

        # Delete the created user record.
        def test_user(self):
            storage = self.app.app.wrap_app.app.storage
            uid = self.user_info.get('uid')
            storage.del_user(uid, True)
            user = storage.get_user_info(uid)
            self.assertEqual(user, None)

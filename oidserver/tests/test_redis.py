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

from webtest import TestApp
from oidserver.wsgiapp import make_app
from oidserver.tests import test_config

REDIS = False
try:
    if 'redis' in test_config.get('oidstorage.backend','memory'):
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
                    'auth.backend': 'services.auth.dummy.DummyAuth',
                    'oidstorage.backend':
                        'oidserver.storage._redis.RedisStorage',
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

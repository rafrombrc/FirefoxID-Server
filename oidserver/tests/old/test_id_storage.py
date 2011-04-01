# -*- coding: utf-8 -*-
import unittest
import urlparse

from webtest import TestApp
from oidserver.storage.id_storage import ID_Storage
from oidserver.controllers import auth
"""
"""


class FakeRequest(object):
    """
     Fake request object for testing only
    """

    def __init__(self, path, environ={}, post={}, get={}):
        self.scheme = 'http'
        self.host = 'evilonastick.com'
        self.path_info = path
        self.environ = environ
        self.POST = post
        self.params = get


class TestIDStorage(unittest.TestCase):

    def setUp(self):
        # use a default 'dummy' config file.
        config = {
            'oidstorage.backend': 'memory',
            'auth.sqlurl': 'sqlite:///:memory:',
            'oid.host': 'http://localhost',
            'oid.assoc_expires_in': 3600,
            'site.host': 'jrconlin.com',
            'site.secret_salt': 'salt'}
        self.idstore = ID_Storage(config=config)

    def test_site_assoc(self):
        request = FakeRequest(path='/foo')
        uid = 1234
        # so we can compare later
        userInfo = {u'uid': uid,
                    u'pemail': u'foo@example.com',
                    u'sname': u'bob',
                    u'fname': u'jones',
                    u'avatar': u'http://example.com/test.jpg',
                    u'nickname': u'jRandomUser',
                    u'poco_server': u'http://poco.example.com'}
        site_id = self.idstore.gen_site_id(uid,request)
        site_secret = self.idstore.gen_site_secret(site_id,request)

        assoc = self.idstore.set_site_association(site_id, request,
                                          uid=uid, secret=site_secret)
        self.assertEqual(self.idstore.set_user_info(**userInfo),True)
        assoc2 = self.idstore.get_association_by_uid(uid,request)
        assoc3 = self.idstore.get_association_by_site(site_id,request)
        for key in assoc.keys():
            self.assertEqual(assoc[key],assoc2[key])
            self.assertEqual(assoc[key],assoc3[key])
        user2 = self.idstore.get_user_info(uid)
        self.assertEqual(userInfo,user2)
from cPickle import loads, dumps
from collections import defaultdict
from datetime import datetime
from hashlib import sha1
from oidserver.storage import OIDStorage, OIDStorageException
from oidserver.storage.oidstoragebase import OIDStorageBase
from services import logger
from services.util import randchar

import redis
import time


class RedisStorage(OIDStorage, OIDStorageBase):
    prefix = 'id'

    def __init__(self, host='127.0.0.1', port=6379, database='id', **kw):
        self.prefix = database
        self._db = redis.Redis(host)

    @classmethod
    def get_name(self):
        return 'redis'

    #
    # Redirect Helpers
    #
    def add_redirect(self, url, site, handle):
        token = sha1(url).hexdigest()
        dump = dumps((url, site, handle))
        self._db.set(token, dump)
        return token

    def get_redirect(self, token):
        return loads(self._db.get(token))

    #
    # Association APIs
    #
    def set_association(self, uid, request,
                        site_id = None,
                        handle = None,
                        secret = None,
                        email = None,
                        perms = 0,
                        state = 1,
                        **kw):

        if handle is None:
            handle = self.get_assoc_handle(uid, request)
            if handle is None:
                raise OIDStorageException("Invalid handle specified")
        if secret is None:
            secret = self.gen_site_secret(request)
        if email is None:
            email = self.get_user_info(uid).get('pemail')
        handle = "assoc_" + handle
        dump = dumps((secret, assoc_type, private))
        self._db.set(handle, dump)

    def get_association(self, handle):
        secret = self._db.get(handle)
        if secret is None:
            raise KeyError(handle)
        return loads(secret)

    def del_association(self, handle):
        """Removes the association and all its sites"""
        self._db.delete(handle)
        self._db.delete('%s:sites' % handle)

    #
    # Site : sites associated with an association handle
    #
    def add_site(self, handle, site):
        ttl = self._db.ttl(handle)
        if ttl == -1:
            # oops the association handle is gone
            raise KeyError(handle)
        key = '%s:sites' % handle
        if not self._db.sismember(key, site):
            self._db.sadd(key, site)
        self._db.expire(key, ttl)

    def get_sites(self, handle):
        key = '%s:sites' % handle
        return self._db.smembers(key)

    def check_auth(self, handle, site):
        key = '%s:sites' % handle
        return self._db.sismember(key, site)

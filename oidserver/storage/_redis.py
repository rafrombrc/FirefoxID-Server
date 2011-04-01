from cPickle import loads, dumps
from hashlib import sha1
import redis


class RedisStorage(object):

    def __init__(self, host='127.0.0.1'):
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
    def add_association(self, handle, secret, assoc_type, private=False,
                        expires_in=3600):
        dump = dumps((secret, assoc_type, private))
        self._db.setex(handle, dump, expires_in)

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

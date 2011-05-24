from cPickle import loads, dumps
from collections import defaultdict
from datetime import datetime
from hashlib import sha1
from oidserver.storage import OIDStorage, OIDStorageException
from oidserver.storage.oidstoragebase import OIDStorageBase
from services import logger
from services.util import randchar

# TODO: should I switch to cJson for data storage?

import redis
import time


class RedisStorage(OIDStorage):
    prefix = 'id'
    USER_DB = 'user_'
    VALID_DB = 'validate_'

    def __init__(self, host='127.0.0.1', port=6379, database='id', **kw):
        self.prefix = database
        self._db = redis.Redis(host)

    @classmethod
    def get_name(self):
        return 'redis'

    def get_address_info(self, uid, email_address):
        addr_info = self._db.get('%s%s' % (self.USER_DB, uid),
                            {}).get('emails', {}).get(email_address, None)
        if addr_info is not NOne:
            addr_info['email'] = email_address
            addr_info['uid'] = uid
        return addr_info

    def get_user_info(self, uid):
        return loads(self._db.get('%s%s' % (self.USER_DB, uid)))

    def set_user_info(self, uid, info):
        self._db.set('%s%s' % (self.USER_DB, uid), dumps(info))

    def get_addresses(self, uid, filter = None ):
        addrs = self._db.get('%s%s' % (self.USER_DB, uid), {}).get('emails')
        if addrs is None:
            return None
        list = []
        for addr in addrs:
            if (filter is not None and
                addrs.get(addr).get('state', None) != filter):
                continue
            list.append(addr)
        return list

    def set_address_info(self, uid, email_address, info):
        info = self.get_user_info(uid)
        if info is None:
            info = {'emails': {}}
        info['emails'][email_address] = info
        self.set_user_info(uid, info)
        return self.get_address_info(uid, email_address)

    def set_user_info(self, uid, info=None, **kw):
        self._db.set(uid, dumps(info))

    def del_user(self, uid, confirmed = False):
        if confirmed:
            self._db.delete('%s%s' % (self.USER_DB,uid))

    def add_validation(self, uid, email):
        rtoken = ''.join([randchar() for i in range(26)])
        validation_record = {'uid': uid,
                             'created': datetime.now(),
                             'email': email}
        user_info = self._user_db.get(uid,None)
        if user is None:
            logger.error("Could not find user record for uid %s" % uid)
            raise OIDStorageException("uid not found")
        try:
            user =  loads(user_info)
        except (TypeError, EOFError), ex:
            logger.error("Unpickling error %s " % ex)
            raise (OIDStorageException("Storage error"))
        if 'unv_emails' not in user:
            user['unv_emails'] = {}
        user['unv_emails'][email.encode('ascii')] = \
                {'created': int(time.time()),
                 'conf_code': rtoken}
        self._db.set('%s%s' % (self.USER_DB,uid), user)
        self._db.set('validate_%s' % rtoken, validation_record)
        return rtoken

    def get_validation_token(self, uid, email):
        user_info = self._db.get('%s%s' % (self.USER_DB, uid))
        if user_info is None:
            logger.warn('No user information found for uid %s' % uid)
            return None
        user = loads(user_info)
        aemail = email.encode('ascii')
        if aemail in user.get('unv_emails',{}):
            return user.get('unv_emails').get(aemail,
                                              {} ).get('conf_code', None)
        logger.info('No validation token found for uid %s ' % uid)
        return None

    def remove_unvalidated(self, uid, email):
        user_info = self._db.get('%s%s' % (self.USER_DB, uid))
        if user_info is None:
            logger.warn('No user information found for uid %s' % uid)
            return False
        user = loads(user_info)
        if email in user.get('unv_emails', {}):
            rtoken = user.get('unv_emails').get(email,{}).get('conf_code',None)
            if rtoken:
                try:
                    del user['unv_emails'][email]
                    self.set_user_info(uid, user)
                    self._db.delete('validate_%s' % rtoken)
                except KeyError, ex:
                    logger.warn ("Could not remove unvalidated address [%s] "+
                                 " from uid [%s] [%s]" % (email, uid, str(ex)))
                    return False
        return True

    def check_validation(self, uid, token):
        try:
            record = {}
            record_info = self._db.get('%s%s' % (self.VALID_DB, token), None)
            if record_info is not None:
                record = loads(record_info)
                if record.get('uid') == uid:
                    user = self.get_user_info(record.get('uid'))
                    if user is not None:
                        email = record.get('email')
                        user['emails'].append(email)
                        del user['unv_emails'][email]
                        self._db.delete('%s%s', (self.VALID_DB, token))
                    self.set_user_info(uid, user)
                    return True
        except KeyError:
            pass
        return False


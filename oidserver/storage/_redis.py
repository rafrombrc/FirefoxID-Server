from oidserver.storage import OIDStorage, OIDStorageException
from oidserver.storage.oidstoragebase import OIDStorageBase
from services import logger
from services.util import randchar

import redis
import time
import cjson

class RedisStorage(OIDStorage, OIDStorageBase):
    USER_DB = 'user_'
    VALID_DB = 'validate_'

    def __init__(self, host='127.0.0.1', port=6379, database='id', **kw):
        self._db = redis.Redis(host)

    @classmethod
    def get_name(self):
        return 'redis'

    def get_address_info(self, uid, email_address):
        user_info = self.get_user_info(uid)
        if user_info is None:
            return None
        addr_info = user_info.get('emails', {}).get(email_address, None)
        if addr_info is not None:
            addr_info['email'] = email_address
            addr_info['uid'] = uid
        return addr_info

    def check_user(self, uid):
        return ('%s%s' % (self.USER_DB, uid) in self._db)

    def create_user(self, uid, email, base = None, **kw):
        if base is None:
            base = {}
        user_record = base
        user_record['uid'] = uid
        user_record['emails'] = {}
        user_record['primary'] = email
        self.set_user_info(uid, user_record)
        return self.get_user_info(uid)

    def get_user_info(self, uid):
        data = self._db.get('%s%s' % (self.USER_DB, uid))
        if data:
            return cjson.decode(data)
        else:
            return None

    def set_user_info(self, uid, info):
        self._db.set('%s%s' % (self.USER_DB, uid), cjson.encode(info))

    def get_addresses(self, uid, filter = None ):
        user_info = self.get_user_info(uid)
        if user_info is None:
            return None
        addrs = user_info.get('emails')
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
        self._db.set("%s%s" % (self.USER_DB,uid), cjson.encode(info))

    def del_user(self, uid, confirmed = False):
        if confirmed:
            self._db.delete('%s%s' % (self.USER_DB, uid))

    def add_validation(self, uid, email):
        rtoken = ''.join([randchar() for i in range(26)])
        validation_record = {'uid': uid,
                             'created': time.time(),
                             'email': email}
        user_info = self._db.get('%s%s' % (self.USER_DB, uid))
        if user_info is None:
            logger.error("Could not find user record for uid %s" % uid)
            raise OIDStorageException("uid not found")
        try:
            user =  cjson.decode(user_info)
        except (TypeError, EOFError), ex:
            logger.error("Unpickling error %s " % ex)
            raise (OIDStorageException("Storage error"))
        user['emails'][email.encode('ascii')] = \
                {'created': int(time.time()),
                 'state': 'pending',
                 'conf_code': rtoken}
        self.set_user_info(uid, user)
        self._db.set('%s%s' % (self.VALID_DB,rtoken),
                     cjson.encode(validation_record))
        return rtoken

    def get_validation_token(self, uid, email):
        user_info = self._db.get('%s%s' % (self.USER_DB, uid))
        if user_info is None:
            logger.warn('No user information found for uid %s' % uid)
            return None
        user = cjson.decode(user_info)
        aemail = email.encode('ascii')
        if (aemail in user.get('emails',{}) and
            user['emails'][aemail].get('state', None) == 'pending'):
            return user['emails'][aemail].get('conf_code', None)
        logger.info('No validation token found for uid %s ' % uid)
        return None

    def remove_unvalidated(self, uid, email):
        user_info = self._db.get('%s%s' % (self.USER_DB, uid))
        if user_info is None:
            logger.warn('No user information found for uid %s' % uid)
            return False
        user = cjson.decode(user_info)
        if (email in user.get('emails', {}) and
            user['emails'][email].get('state', None) == 'pending'):
                rtoken = user['emails'][email].get('conf_code',None)
                if rtoken:
                    try:
                        del user['emails'][email]
                        self.set_user_info(uid, user)
                        self._db.delete('validate_%s' % rtoken)
                    except KeyError, ex:
                        logger.warn ("Could not remove unvalidated " +
                                     "address [%s] from uid [%s] [%s]" %
                                     (email, uid, str(ex)))
                        return False
        return True

    def check_validation(self, uid, token):
        try:
            record = None
            record_info = self._db.get('%s%s' % (self.VALID_DB, token))
            if record_info is not None:
                record = cjson.decode(record_info)
                if record.get('uid') == uid:
                    user = self.get_user_info(record.get('uid'))
                    if user is not None:
                        import pdb; pdb.set_trace();
                        email = record.get('email')
                        if user['emails'][email].get('state',
                                                     None) == 'pending':
                            user['emails'][email]['state'] = 'verified'
                        if 'conf_code' in user['emails'][email]:
                            del user['emails'][email]['conf_code']
                        self._db.delete('%s%s', (self.VALID_DB, token))
                    self.set_user_info(uid, user)
                    return record.get('email')
        except KeyError:
            pass
        return False

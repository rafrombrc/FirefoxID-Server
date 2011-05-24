from collections import defaultdict
from datetime import datetime
from hashlib import sha1
from oidserver.storage import OIDStorage, OIDStorageException
from oidserver.storage.oidstoragebase import OIDStorageBase
from services import logger
from services.util import randchar
import time
import types


class MemoryStorage(OIDStorage, OIDStorageBase):

    def __init__(self, **kw):
        self.sites = defaultdict(list)
        self._user_db = {}
        self._validate_db = {}

    @classmethod
    def get_name(self):
        return 'memory'

#User
    def get_address_info(self, uid, email_address):
        addr_info = self._user_db.get(uid,
                        {}).get('emails', {}).get(email_address, None)
        if addr_info is not None:
            addr_info['email'] = email_address
            addr_info['uid'] = uid
        return addr_info

    def get_user_info(self, uid):
        return self._user_db.get(uid, None)

    def get_addresses(self, uid, filter = None):
        addrs = self._user_db.get(uid, {}).get('emails')
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
        self._user_db[uid] = info

    def del_user(self, uid, confirmed = False):
        if confirmed:
            del self._user_db[uid]
            return True
        else:
            return False

    def add_validation(self, uid, email):
        rtoken = ''.join([randchar() for i in range(26)])
        validation_record = {u'uid': uid,
                             u'created': datetime.now(),
                             u'email': email}
        user = self._user_db.get(uid,None)
        if user is None:
            raise OIDStorageException("uid not found")
        if 'unv_emails' not in user:
            user['unv_emails'] = {}
        user['unv_emails'][email.encode('ascii')] = \
                {'created': int(time.time()),
                 'conf_code': rtoken}
        self._user_db[uid] = user
        self._validate_db[rtoken] = validation_record
        return rtoken

    def get_validation_token(self, uid, email):
        user = self._user_db.get(uid,None)
        if user is None:
            return None
        if email in user.get('unv_emails',{}):
            return user.get('unv_emails').get(email, {}).get('conf_code', None)
        return None

    def remove_unvalidated(self, uid, email):
        user = self._user_db[uid]
        if email in user['unv_emails']:
            rtoken = user['unv_emails'][email]['conf_code']
            try:
                del user['unv_emails'][email]
                self._user_db[uid] = user
                del self._validate_db[rtoken]
            except KeyError:
                return False
        return True

    def check_validation(self, uid, token):
        try:
            record = self._validate_db.get(token, None)
            if record is not None and record.get('uid') == uid:
                user = self._user_db.get(uid)
                if user is not None:
                    email = record['email']
                    user['emails'].append(email)
                    del user['unv_emails'][email]
                    del self._validate_db[token]
                self._user_db[uid] = user
                return True
        except (KeyError), ofe:
            logger.error("Could not validate token %s [%s]",
                         token, str(ofe))
            raise OIDStorageException("Could not validate token")
        return False

    def purge_validation(self, config = None):
        return True

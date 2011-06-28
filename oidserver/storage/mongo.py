from datetime import datetime
from oidserver.storage import OIDStorage, OIDStorageException
from pymongo.errors import OperationFailure
from services import logger
from services.util import randchar
import pymongo
import time


class MongoStorage(OIDStorage):
    """ Store data into a Mongo instance """

    def __init__(self, host = '127.0.0.1', port = 27017, database = 'id'):
        """
            note: arguments here must match corresponding values in the .conf
            file or else the process will not start.
            e.g.
            [oidstorage]
            backend = mongo
            host    = localhost
            port    = 27017
        """
        self._connection = pymongo.Connection(host, port)
        self._connection[database]
        self._user_db = self._connection[database].user
        """ _user schema:
            _id     user id
            pemail  primary email
            emails  verified email list
            name    user name
            data    non-indexable user data elements (e.g. avatar,
                        poco_server, preferred nickname, etc.)
            assocs  Association ids
        """
        self._validate_db = self._connection[database].validate
        """
            _validate schema:
            _id     validation code
            uid     user id
            email   unverified email address
        """

    @classmethod
    def get_name(self):
        return 'mongo'

    def get_address_info(self, uid, email_address):
        user = self.get_user_info(uid)
        if not user:
            return {}
        addr_info = user.get('emails', {}).get(email_address, None)
        if addr_info is not None:
            addr_info['email'] = email_address
            addr_info['uid'] = uid
        return addr_info

    def check_user(self, uid):
        return self._user_db.find_one({u'_id': uid}) is not None

    def create_user(self, uid, email, base = None, **kw):
        if base is None:
            base = {}
        user_record = base
        user_record['emails'] = {}
        user_record['primary'] = email
        self.set_user_info(uid, user_record)
        return self.get_user_info(uid)

    def get_user_info(self, uid):
        try:
            return self._user_db.find_one({u'uid': uid})
        except OperationFailure, ofe:
            logger.error("Could not fetch info for uid [%s], [%s]" % (uid,
                                                                    str(ofe)))
            raise OIDStorageException()

    def get_addresses(self, uid, filter = None):
        addrs = self.get_user_info.get('emails')
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
        if info is None:
            return self.del_user(uid, confirmed = True)
        info[u'_id'] = uid
        self._user_db.save(info, safe = True)

    def del_user(self, uid, confirmed = False):
        if confirmed:
            self._user_db.remove({u'_id': uid}, safe = True)
            return True
        else:
            return False

    def add_validation(self, uid, email):
        rtoken = ''.join([randchar() for i in range(26)])
        validation_record = {u'uid': uid,
                             u'created': datetime.now(),
                             u'email': email}
        user = self._user_db.get(uid, None)
        if user is None:
            raise OIDStorageException("uid not found")
        if 'emails' not in user:
            user['emails'] = {}
        user['emails'][email.encode('ascii')] = \
                {'created': int(time.time()),
                 'state': 'pending',
                 'conf_code': rtoken}
        self.set_user_info(uid, user)
        validation_record[u'_id'] = rtoken
        self._validate_db.save(validation_record)
        return rtoken

    def get_validation_token(self, uid, email):
        user = self._user_db.find_one({u'_id': uid})
        if user is None:
            return None
        if (email in user.get('emails', {}) and
            user['emails'][email].get('state', None) == 'pending'):
            return user['emails'][email].get('conf_code', None)
        return None

    def remove_email(self, uid, email, state = 'pending'):
        user = self._user_db[uid]
        if (email in user['emails'] and
            user['emails'][email].get('state', None) == state):
                rtoken = user['emails'][email].get('conf_code', None)
                try:
                    del user['emails'][email]
                    self.set_user_info(uid, user)
                    if rtoken:
                        self._validate_db.remove({'_id': rtoken})
                except (KeyError, OperationFailure):
                    logger.warn('Could not remove email %s from user %s'
                                % (email, uid));
                    return False
        return True

    def check_validation(self, uid, token):
        try:
            record = self._validate_db.find_one({u'_id': token})
            if record is not None and record.get('uid') == uid:
                user = self._user_db.get(uid)
                if user is not None:
                    email = record['email']
                    user['emails'].append(email)
                    del user['emails'][email]
                    self._validate_db.remove({u'_id': token})
                self.set_user_info(uid, user)
                return True
        except (KeyError), ofe:
            logger.error("Could not validate token %s [%s]",
                         token, str(ofe))
            raise OIDStorageException("Could not validate token")
        return False

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
from collections import defaultdict
from datetime import datetime
from oidserver.storage import OIDStorage, OIDStorageException
from oidserver.storage.oidstoragebase import OIDStorageBase
from services import logger
from services.util import randchar
import time


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

    def check_user(self, uid):
        return uid in self._user_db

    def create_user(self, uid, email, base = None, **kw):
        if base is None:
            base = {}
        user_record = base
        user_record['uid'] = uid
        user_record['emails'] = {}
        user_record['primary'] = email
        self._user_db[uid] = user_record
        return self._user_db[uid]

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

    def set_user_info(self, uid, info = None, **kw):
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
        user = self._user_db.get(uid, None)
        if user is None:
            raise OIDStorageException("uid not found")
        if 'emails' not in user:
            user['emails'] = {}
        user['emails'][email.encode('ascii')] = \
                {'created': int(time.time()),
                 'conf_code': rtoken,
                 'state': 'pending'}
        self._user_db[uid] = user
        self._validate_db[rtoken] = validation_record
        return rtoken

    def get_validation_token(self, uid, email):
        user = self._user_db.get(uid, None)
        if user is None:
            return None
        if email in user.get('emails', {}):
            return user.get('emails').get(email, {}).get('conf_code', None)
        return None

    def remove_email(self, uid, email, state = 'pending'):
        user = self._user_db[uid]
        if email in user['emails']:
            if user['emails'][email].get('state', None) == state:
                rtoken = user['emails'][email]['conf_code']
                try:
                    del user['emails'][email]
                    self._user_db[uid] = user
                    if rtoken in self._validate_db:
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
                    # only deal with 'pending' records.
                    if user['emails'][email].get('state', None) == 'pending':
                        user['emails'][email]['state'] = 'verified'
                        # Remove the old valiation code
                    if 'conf_code' in user['emails'][email]:
                        del user['emails'][email]['conf_code']
                    del self._validate_db[token]
                self._user_db[uid] = user
                return True
        except (KeyError), ofe:
            logger.error("Could not validate token %s [%s]",
                         token, str(ofe))
            raise OIDStorageException("Could not validate token")
        return False

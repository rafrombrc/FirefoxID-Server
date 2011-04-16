from collections import defaultdict
from hashlib import sha1
from oidserver.storage import OIDStorage, OIDStorageException
from oidserver.storage.oidstoragebase import OIDStorageBase
import time


class MemoryStorage(OIDStorage, OIDStorageBase):

    def __init__(self, **kw):
        self.sites = defaultdict(list)
        self.redirects = {}
        self._assoc_db = {}
        self._user_db = {}

    @classmethod
    def get_name(self):
        return 'memory'

    def add_redirect(self, url, site, handle):
        token = sha1(url).hexdigest()
        self.redirects[token] = url, site, handle
        return token

    def get_redirect(self, token):
        return self.redirects[token]

    def add_site(self, site, handle):
        if site in self.sites[handle]:
            return
        self.sites[handle].append(site)

    def get_sites(self, handle):
        return self.sites[handle]

    def check_auth(self, handle, site):
        return site in self.sites[handle]

#Association
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
        self._assoc_db[handle] = {u'site_id': site_id,
                                  u'uid': uid,
                                  u'secret': secret,
                                  u'email': email,
                                  u'perms': perms,
                                  u'created': int(time.time()),
                                  u'state': state}
        return self._assoc_db[handle]

    def set_assoc_state(self, assoc_handle, state):
        if assoc_handle not in self._assoc_db:
            return False
        self._assoc_db[assoc_handle]['state'] = state
        return True

    def get_associations_by_email(self, email, handle = None):
        results = []
        for handle, hash in self._assoc_db.iteritems():
            match = True
            if hash.get('email', False) != email:
                match = False
            if handle is not None and handle != handle:
                match = False
            if match:
                results.append({handle: hash})
        return results

    def get_association_by_email(self, request, email):
        site_id = self.gen_site_id(request)
        for handle, hash in self._assoc_db.iteritems():
            if (hash.get('email', '') == email and
                hash.get('site_id', '') == site_id):
                    return hash
        return None

    def get_association(self, handle):
        if handle not in self._assoc_db:
            return None
        return self._assoc_db[handle]

    def get_associations_for_uid(self, uid):
        result = []
        for handle, hash in self._assoc_db.iteritems():
            if hash.get('uid','') == uid:
                result.append(hash)
        return result


    def del_association(self, handle):
        if handle not in self._assoc_db:
            return False
        del self._assoc_db[handle]
        return True

    def get_emails(self, uid, handle):
        if uid not in self._user_db:
            return {}
        result = {u'default': self._user_db[uid]['pemail']}
        if 'emails' in self._user_db[uid]:
            result['emails'] = self._user_db[uid]['emails']
        else:
            result['emails'] = []
        return result

#User
    def get_user_info(self, uid):
        return self._user_db.get(uid, None)

    def create_user(self, uid, pemail = None,
                      sname = "",
                      fname = "",
                      emails = [],
                      unverified_emails = [],
                      data = {'default_perms': 0},
                      **kw):
        # Must supply either pemail or emails
        if len(emails) == 0 and pemail is None:
            raise OIDStorageException("Must supply at least one email")
        # No list of emails? Append the primary.
        if len(emails) == 0:
            emails.append(pemail)
        # No primary? Take the first from the list of emails.
        if pemail is None:
            pemail = emails[0]
        user_record = {u'uid': uid,
                       u'pemail': pemail,
                       u'emails': emails,
                       u'unv_emails': unverified_emails,
                       u'fname': fname,
                       u'sname': sname,
                       u'data': data}
        self._user_db[uid] = user_record

    def update_user(self, uid, user):
        record = self._user_db.get(uid)
        if record is None:
            return False
        for key in user.keys():
            if key != "_id":
                record[key]=user.get(key)
        self._user_db[uid] = record
        return record

    def del_user(self, uid, request, confirmed=False):
        if confirmed:
            handle = self.get_assoc_handle(uid, request)
            del self._user_db[handle]
            return True
        else:
            return False

    def add_validation(self, uid, email):
        rtoken =  ''.join([randchar() for i in range(26)])
        validation_record = {u'uid': uid,
                             u'created': datetime.now(),
                             u'email': email}
        user = self._user_db[uid]
        user['unv_emails'][email] = {'created': int(time.time()),
                                 'conf_code': rtoken}
        self._user_db[uid]=user
        self._validate_db[rtoken] = validation_record
        return rtoken

    def get_validation_token(self, uid, email):
        for key in self._validate_rb.keys():
            if (self._validate_rb[key].get('uid') == uid and
                self._validate_rb[email].get('email') == email):
                return key
        return None

    def remove_unvalidated(self, uid, email):
        user = self._user_db[uid]
        if email in user['unv_emails']:
            rtoken = user['unv_emails'][email]['conf_code']
            try:
                del user['unv_emails'][email];
                self._user_db[uid]=user
                del self._validate_db[rtoken]
            except KeyError:
                return false
        return true

    def check_validation(self, token):
        try:
            record = self._validate_db.get(token, None)
            if record is not None:
                user = self._user_db.get({u'_uid': uid})
                if user is not None:
                    user['emails'].append(record['email'])
                    del self._validate_db[token]
                self._user_db.save(user)
                return True
        except (OperationFailure, KeyError) as ofe:
            logger.error("Could not validate token %s [%s]",
                         token, str(ofe))
            raise OIDStorageException("Could not validate token")

    def purge_validation(self, config = None):
        return True

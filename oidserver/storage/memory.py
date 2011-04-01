from collections import defaultdict
from hashlib import sha1
from oidserver.storage import OIDStorage, OIDStorageException
from oidserver.storage.oidstoragebase import OIDStorageBase
import time


class MemoryStorage(OIDStorage, OIDStorageBase):

    def __init__(self):
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

    def set_user_info(self, uid, pemail = None,
                      sname = "",
                      fname = "",
                      emails = [],
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
                       u'fname': fname,
                       u'sname': sname,
                       u'data': data}
        self._user_db[uid] = user_record

    def del_user(self, uid, request, confirmed=False):
        if confirmed:
            handle = self.get_assoc_handle(uid, request)
            del self._user_db[handle]
            return True
        else:
            return False

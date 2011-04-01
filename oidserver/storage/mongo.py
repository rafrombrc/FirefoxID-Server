from oidserver.storage import OIDStorage, OIDStorageException
from oidserver.storage.oidstoragebase import OIDStorageBase
from pymongo.errors import OperationFailure
from services import logger
import json
import pymongo
import time


class MongoStorage(OIDStorage, OIDStorageBase):
    """ Store data into a Mongo instance """

    def __init__(self, host='127.0.0.1', port=27017, database='id'):
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
        self._redir_db = self._connection[database].redir
        self._assoc_db = self._connection[database].assoc
        """ _assoc schema:
            _id     (generated)
            handle  unique row id: ("site_id-uid")
            uid     user id
            site_id site_id (remote domain, e.g. "example.org")
            email   associated email id
            secret  site secret (used for site auth)
            perms   site permissions mask
            created UTC of creation
            state   boolean active/inactive flag
        """
        self._user_db = self._connection[database].user
        """ _user schema:
            _id     user id
            pemail  primary email
            emails  email list
            sname   Surname
            fname   Family name
            data    non-indexable user data elements (e.g. avatar,
                        poco_server, preferred nickname, etc.)
        """

    @classmethod
    def get_name(self):
        return 'mongo'

    #
    # Redirect Helpers
    #
    def add_redirect(self, url, site, handle):
        self._redir_db.insert({u'url': url,
                           u'site': site,
                           u'_id': handle})
        return handle

    def get_redirect(self, url):
        return json.loads(self._redir_db.find_one({u'url': url}))

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
        """
        Add or modify a users association record.
        """
        if handle is None:
            handle = self.get_assoc_handle(uid, request)
        if site_id is None:
            site_id = self.gen_site_id(request)
        if secret is None:
            secret = self.gen_site_secret(request)
        if email is None:
            email = self.get_user_info(uid).get('pemail')
        try:
            assoc_data = {u'handle': handle.lower(),
                           u'site_id': site_id,
                           u'uid': uid,
                           u'secret': secret,
                           u'email': email,
                           u'perms': perms,
                           u'created': int(time.time()),
                           u'state': state}
            self._assoc_db.update({'handle': handle.lower(),
                                         'email': email},
                                        assoc_data,
                                        upsert=True)
            # return assoc_data
            return self._assoc_db.find_one({'handle': handle.lower(),
                                            'email': email})
        except OperationFailure as ofe:
            logger.error("Can't store association %s for %s [%s]" %
                         (handle, uid, str(ofe)))
            raise OIDStorageException("Could not generate association")
        return None

    def set_assoc_state(self, handle, state):
        """ set to indicate log in state (True or False) """
        try:
            self._assoc_db.update({u'handle': handle.lower()},
                                  {'$set': {u'state': state}})
            return True
        except OperationFailure as ofe:
            logger.error("Could not set the assoc state for %s: %s [%s]",
                         (handle.lower(), state, str(ofe)))
            raise OIDStorageException("Could not store state")

    def get_association(self, handle):
        """ get the list of associations per id+siteloc (remember, users
        can have more than one email per site. Each Assoc record reflects
        that)
        """
        if handle is None:
            return None
        try:
            assoc = self._assoc_db.find_one({u'handle': handle.lower()})
        except OperationFailure as ofe:
            raise OIDStorageException(
                "Could not find association with handle %s [%s]" %
                (handle.lower(), str(ofe)))
        # The return value may be None if the assocation has not yet been made
        return assoc

    def get_association_by_email(self, request, email):
        try:
            assoc = self._assoc_db.find_one({u'email': email,
                                        u'site_id': self.gen_site_id(request)})
        except OperationFailure as ofe:
            raise OIDStorageException(
                "Could not find association from email %s [%s]" %
                (email, str(ofe)))
        return assoc

    def get_associations_by_email(self, email, handle = None):
        """ return all associations for this handle + email """
        results = []
        searchObj = {}
        if email is None:
            return results
        else:
            searchObj[u'email'] = email
        if handle is not None:
            searchObj[u'handle'] = handle
        try:
            associations = self._assoc_db.find(searchObj)
            for assoc in associations:
                results.append(assoc)
        except OperationFailure as ofe:
            raise OIDStorageException("Cound not find associations [%s]",
                                        str(ofe))
        return results

    def del_association(self, handle, email = None):
        """Removes the association """
        if handle is None:
            return False
        del_obj = {u'handle': handle.lower()}
        if email is not None:
            del_obj[u'email'] = email
        try:
            self._assoc_db.remove(del_obj)
        except OperationFailure as ofe:
            raise OIDStorageException("Could not remove record %s [%s]" %
                                      (handle.lower(), str(ofe)))
        return True

    def get_emails(self, uid, handle):
        user_info = self.get_user_info(uid)
        try:
            assoc = self.get_association(handle)
            if assoc is not None:
                assoc = assoc[0]
        except KeyError:
            assoc = None
        if user_info is None:
            return {}
        try:
            default = ''
            if assoc is not None:
                default = assoc.get('email')
            if default == '':
                default = user_info.get('pemail')
            result = {u'default': default,
                      u'emails': user_info.get('emails')}
            return result
        except KeyError:
            return {}

    def get_associations_for_uid(self, uid):
        result = []
        try:
            associations = self._assoc_db.find({u'uid': uid})
        except OperationFailure as ofe:
            raise OIDStorageException(
                "Could not find associations for %s [%s]" % (uid, str(ofe)))
        for assoc in associations:
            result.append(assoc)
        # if this is none, should I try a long form lookup?
        return result

    def get_user_info(self, uid):
        try:
            return self._user_db.find_one({u'_id': uid})
        except OperationFailure as ofe:
            raise OIDStorageException(
                "Could not find association for %s [%s]" % (uid, str(ofe)))

    def set_user_info(self, uid, pemail = None,
                      sname = "",
                      fname = "",
                      emails = [],
                      data = {u'default_perms': 0},
                      **kw):
        """There's no real concept of "modify" here. You're updating the
           entire record.
        """
        if pemail is None and len(emails) == 0:
            raise OIDStorageException("Must supply at least one email")
        if len(emails) == 0:
            emails.append(unicode(pemail))
        if pemail is None:
            pemail = emails[0]
        try:
            user_record = {u'_id': uid,
                             u'pemail': unicode(pemail),
                             u'emails': emails,
                             u'sname': unicode(sname),
                             u'fname': unicode(fname),
                             u'data': data
                             }
            self._user_db.save(user_record)
            return user_record
        except OperationFailure as ofe:
            logger.error("Could not set user info for %s [%s]" %
                            (uid, str(ofe)))
            raise OIDStorageException("Could not store user record")

    def del_user(self, uid, confirmed = False):
        if not confirmed:
            return False
        #delete the associated user and associations.
        # NOTE: This presumes that the user has confirmed
        self._assoc_db.remove({u'uid': uid})
        self._user_db.remove({u'_id': uid})
        return True

    #
    # Site : sites associated with an association handle
    #
    def get_sites(self, user_id):
        return self.get_associations_for_uid(user_id)

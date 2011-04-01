""" Store and access user information contained in LDAP served databases

    uses the following config keys:

    auth.sqluri     = Storage
    site.host       = local host (post-fixed to generated id as an email addr)
    site.
"""
import datetime
import ldap
import random

from hashlib import sha1, sha256

# table creation
from sqlalchemy.ext.declarative import declarative_base, Column
from sqlalchemy import create_engine
# column types
from sqlalchemy import Integer, String, Text, DateTime, SmallInteger
# query related calls
from sqlalchemy.sql import bindparam, select, insert, delete, update, and_

from services.util import (generate_reset_code, check_reset_code, ssha,
                           BackendError)
from services.auth import NodeAttributionError
from services.auth.ldappool import ConnectionPool
from services.auth.ldapsql import LDAPAuth
from services import logger

import json
import time
import re

_Base = declarative_base();

class UserInfo(_Base):
    __tablename__ = 'id_user_info'

    # main UID (index)
    uid = Column(Integer, primary_key = True, nullable = False, index=True)
    # primary email (index)
    pemail = Column(String(200), index=True)
    # Surname
    sname = Column(String(100))
    # Family
    fname = Column(String(100))
    # avatar image
    avatar = Column(Text)
    # user's preferred nickname
    nickname = Column(String(100))
    # Portable Contacts Server URL
    poco_server = Column(Text)
    email_list = Column(Text)


class SiteIdToUID(_Base):
    __tablename__ = 'id_site_to_uid'

    # Only required for table creation
    mid = Column(Integer, primary_key=True)
    # The RP domain (index + site_id)
    site = Column(String(100), index=True, nullable = False)
    # the remote site ID (index + site)
    # site_id = Column(String(200), index=True, nullable = False)
    # the local user id (provided by services.auth) (index)
    uid = Column(Integer, index=True, nullable = False)
    # secret (used for site confirmation)
    secret = Column(String(32),  nullable = False)
    # the UTC timestamp when the field was created
    created = Column(Integer, nullable = False)
    # the UTC timestamp when the row was last accessed
    accessed = Column(Integer, nullable = False)
    # the state of the connection (0 = inactive, 1 = active)
    state = Column(SmallInteger, nullable = False)
    # what meta data this site has been granted permission to access
    permissions = Column(Integer)

site_id_to_uid = SiteIdToUID.__table__
user_info = UserInfo.__table__

tables = [site_id_to_uid, user_info]

class ID_Storage(object):
    """ Manage user info and site associations """

    def __init__(self,
                 uid=None,
                 config={},
                 bind_user='binduser',
                 bind_password='binduser',
                 reset_on_return=True,
                 create_tables=True,
                 **kw):

        self.uid = uid
        self.config = config
        self.bind_user = bind_user
        self.bind_password = bind_password
        self.sqluri = config.get('auth.sqluri')
        sqlkw = { 'logging_name': 'idserver'}

        if self.sqluri is not None:
            if self.sqluri.startswith('mysql'):
                sqlkw['reset_on_return'] = reset_on_return
            self._db= create_engine(self.sqluri, **sqlkw)
            for table in tables:
                table.metadata.bind = self._db
                if create_tables:
                    table.create(checkfirst=True)

    @classmethod
    def get_name(self):
        """Returns the name of the authentication backend"""
        return 'idserver'

    @classmethod
    def row_to_dict(self,res):
        response = {}
        for item in res.items():
            key,value = item
            response[key]=value
        return response


    def _site_loc(self, request):
        return "%s:%s" % (request.scheme,request.host)

    def get_association_by_site(self, site_id, request):
        #look up the user by site_id
        where = and_(site_id_to_uid.c.site_id == site_id,
                     site_id_to_uid.c.site == site_loc)
        query = select([site_id_to_uid]).where(where)
        res = self._db.execute(query)
        res = res.fetchone()
        if res is None:
            logger.debug('No data for %s at %s' % (site_id, site_loc))
            return None
        # return a json object containing the response.
        return self.row_to_dict(res)

    def get_association_by_uid(self, uid, request):
        #look up the user by site_id
        site_loc = self._site_loc(request)
        where = and_(site_id_to_uid.c.uid == uid,
                     site_id_to_uid.c.site == site_loc)
        query = select([site_id_to_uid]).where(where)
        res = self._db.execute(query)
        res = res.fetchone()
        if res is None:
            logger.debug('No data for %s at %s' % (uid, site_loc))
            return None
        # return a json object containing the response.
        return self.row_to_dict(res)

    def set_site_association(self, site_id, request,
                             uid=None,
                             secret='',
                             permissions={},
                             **kw):
        #record the site info.
        if uid is None:
            uid = self.uid
        site_loc = self._site_loc(request)
        parms = {'site': unicode(site_loc),
                'uid': uid,
                'site_id': unicode(site_id),
                'secret': unicode(secret),
                'created': int(time.time()),
                'accessed': int(time.time()),
                'state': 1,
                'permissions': self.as_permission(permissions)}
        query = insert(site_id_to_uid).values(**parms)
        res = self._db.execute(query)
        if res.rowcount != 1 :
            logger.debug('Unable to add site association for %s at %s' %
                         uid, site_loc)
            return None
        return parms

    def forget_site_association(self, site_id, request,
                                uid=None):
        if uid is None:
            uid = self.uid
        if uid is None:
            return False
        if  re.search("[^\w]",uid):
            return False
        site_loc = self._site_loc(request)
        where = _and(site_id_to_uid.c.site_id == site_id,
                     site_id_to_uid.c.site_loc == site_loc)
        query = delete(site_id_to_uid).where(where)
        return True;

    def get_user_info(self, uid=None):
        if uid is None:
            uid = self.uid
        query = select([user_info]).where(user_info.c.uid == uid)
        res = self._db.execute(query)
        row = res.fetchone()
        if row is None and res.closed:
            print ('crap')
            return None
        return self.row_to_dict(row)

    def forget_user(self, uid=None):
        if uid is None:
            return False
        if type(uid) is str: # Sorry little Billy '); Drop Tables *;
            return False
        query = delete([user_info]).where(user_info.c.uid == uid)
        self._db.execute(query)
        return True;

    def set_user_info(self,
                      uid=None,
                      pemail="",
                      sname="",
                      fname="",
                      avatar="",
                      nickname="",
                      poco_server="",
                      **kw):
        if uid is None:
            uid = self.uid
        query = insert(user_info).values(
            uid = uid,
            pemail = pemail,
            sname = sname,
            fname = fname,
            avatar = avatar,
            nickname = nickname,
            poco_server = poco_server)
        res = self._db.execute(query)
        if res.rowcount != 1 :
            logger.debug('Unable to add user info ')
            return False
        return True

    def get_site_id(self, uid, request):
        """ returns the site id """
        userInfo = self.get_association_by_uid(uid,request)
        if userInfo is None or userInfo.site_id is None:
            return None
        return userInfo.site_id

    def gen_site_id(self, uid, request):
        """ Generate a site specific uid """
        # Generate a simple hash of the uid + site host.
        uid_seed = request.scheme + request.host + str(uid)
        # sha256 not for security, but to reduce the chance of collision to
        # near 0
        id = sha256(uid_seed).hexdigest()
        site = self.config.get('site.host','localhost')
        return '%s@%s' % (id, site)

    def get_site_secret(self, site_uid, request):
        return self.gen_site_secret(site_uid, request)

    def gen_site_secret(self, site_uid, request):
        """ Generate site + uid specific secret """
        #offset = int(self.config.get('site.offset',1))
        secret_base = site_uid + self.config.get('site.secret_salt','')
        return sha1(secret_base).hexdigest()

    def get_sites(self,uid=None):
        if uid is None:
            uid = self.uid
        if uid is None:
            return False
        result = []
        query = select([site_id_to_uid]).where(site_id_to_uid.c.uid == uid)
        res = self._db.execute(query)
        row = res.fetchone()
        while row is not None:
            result.append({'mid':row['mid'],
                           'site':row['site'],
                           'site_id':row['site_id'],
                           'created':row['created'],
                           'state':row['state'],
                           'permissions':
                             self.as_permission_list(row['permissions'])})
            row = res.fetchone()
        return result;

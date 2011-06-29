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
import abc
from services.pluginreg import PluginRegistry
from oidserver import logger


class OIDStorageException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self)


class OIDStorage(PluginRegistry):
    """Abstract Base Class for the storage."""
    plugin_type = 'oidstorage'

#Standard methods
    @abc.abstractmethod
    def get_user_info(uid):
        """ Return a dict of user info for the corresponding uid. """

    @abc.abstractmethod
    def check_user(uid):
        """ Return if the UID exists in the user database """

    @abc.abstractmethod
    def set_user_info(uid, info):
        """ Set/Create the user information """

    @abc.abstractmethod
    def get_address_info(uid, email_address):
        """ return info regarding a specific email address for a specific
            uid """

    @abc.abstractmethod
    def get_addresses(uid, filter):
        """ return addressed for email optionally filtered """

#Auth Methods (for stand alone server/IA implementations)
    @abc.abstractmethod
    def add_validation(self, uid, email):
        """ Generate a validation key and log it for a particular user/email
        """

    @abc.abstractmethod
    def check_validation(self, uid, token):
        """ Fetch an email address associated with a token, (verify it's
            owned by the uid), and add it to the list of uid's valid emails
        """

    @abc.abstractmethod
    def get_validation_token(self, uid, email):
        """ Fetch out a validation token for a specific uid/email """

    @abc.abstractmethod
    def remove_email(self, uid, email, state):
        """ remove an email from a user """


def get_storage(config, type='oidstorage'):
    # loading provided storages
    from oidserver.storage.memory import MemoryStorage
    OIDStorage.register(MemoryStorage)
    try:
        from oidserver.storage._redis import RedisStorage
        OIDStorage.register(RedisStorage)
    except ImportError, ex:
        logger.warn("Could not import redis. Has it been installed? [%s]" % ex)
        pass

    try:
        from oidserver.storage.mongo import MongoStorage
        OIDStorage.register(MongoStorage)
    except ImportError, ex:
        logger.warn("Could not import mongo. Has it been installed? [%s]" %
                    ex)
        pass

    return OIDStorage.get_from_config(config)

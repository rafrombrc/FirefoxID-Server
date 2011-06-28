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

import abc
from services.pluginreg import PluginRegistry


class OIDStorageException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self)


class OIDStorage(PluginRegistry):
    """Abstract Base Class for the storage."""
    plugin_type = 'oidstorage'

    @abc.abstractmethod
    def add_redirect(self, url, user, site, handle):
        """Stores a redirect.

        """

    @abc.abstractmethod
    def get_redirect(self, token):
        """Retrieves a redirect
        """

    @abc.abstractmethod
    def get_sites(self, user):
        """Returns all sites a user added an authorization to.

        Args:
           user: User

        Return:
           A sequence of (site, handle)
        """


def get_storage(config, type='oidstorage'):
    # loading provided storages
    from oidserver.storage.memory import MemoryStorage
    OIDStorage.register(MemoryStorage)
    try:
        from oidserver.storage._redis import RedisStorage
        OIDStorage.register(RedisStorage)
    except ImportError:
        pass

    try:
        from oidserver.storage.mongo import MongoStorage
        OIDStorage.register(MongoStorage)
    except ImportError:
        pass

    return OIDStorage.get_from_config(config)

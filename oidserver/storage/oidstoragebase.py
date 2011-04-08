from hashlib import sha1
import urlparse


class OIDStorageBase:

    def get_assoc_handle(self, uid, request, site_loc=None):
        """ Generate a unique association handle
        """
        if site_loc is None:
            site_loc = self.gen_site_id(request)
            if site_loc is None:
                return None
        return "%s-%s" % (uid, site_loc)

    def gen_site_id(self, request):
        """ Generate a site specific Identifier from the request object
        """
        # originally, sep. based on scheme + host.
        audience = request.params.get('audience','')
        if "http:" in audience:
            return urlparse.urlparse(audience).netloc
        else:
            if len(audience):
                return audience
        return ''

    def gen_site_secret(self, request, site_id=None, salt='', **kw):
        """ This should be a calculated secret (for recovery reasons)
        """
        if site_id is None:
            site_id = self.gen_site_id(request)
            if site_id is None:
                return ''
        """ Generate site + uid specific secret """
        secret_base = site_id + salt
        return sha1(secret_base).hexdigest()

    # bit representation of what fields have been granted access
    # permissions to the remote site (powers used for readability)
    _permissions_table = {'name': 2 ** 0,
                          'email': 2 ** 1,
                          'nickname': 2 ** 2,
                          'avatar': 2 ** 3,
                          'poco_server': 2 ** 4}

    @classmethod
    def as_permission(cls, list):
        perm = 0
        for string in list:
            perm |= cls._permissions_table.get(str(string).lower(), 0)
        return perm

    @classmethod
    def as_permission_list(cls, perm):
        list = []
        for name in cls._permissions_table.keys():
            if (perm & self._permissions_table.get(name)):
                list.append(name)
        return list

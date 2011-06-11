from hashlib import sha1
import urlparse


class OIDStorageBase:

    def gen_site_id(self, request):
        """ Generate a site specific Identifier from the request object
        """
        # originally, sep. based on scheme + host.
        audience = request.params.get('audience', '')
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


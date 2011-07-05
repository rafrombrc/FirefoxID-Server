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


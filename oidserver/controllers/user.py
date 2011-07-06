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
from webob.exc import HTTPBadRequest
from webob import Response

from services.util import extract_username
from oidserver.util import get_template
from oidserver.controllers import BaseController

_OP_ROOT = 'https://services.mozilla.com/openid/'


class UserController(BaseController):

    def get_user_info(self, request, **params):
        """ Display the appropriate user page or discovery page """
        user_info = {}
        user = str(request.sync_info['user'])
        params = {'user': user,
                  'host': self.app.config['oid.host'],
                  'config': self.app.config,
                  'request': request }

        uid = self.get_session_uid(request)
        if uid is not None:
            # Convert the user name to a standardized token
            user_name = extract_username(user)
            user_id = self.app.auth.backend.get_user_id(user_name)
            if user_id == uid:
                # hey that's me !
                user_info = self.app.storage.get_user_info(user_id) or {}
                params['user_info'] = user_info
                params['sig'] = self.gen_signature(uid, request)
        # Use the older style of discovery (with link refs)
        template = get_template('user')
        ct = 'text/html'
        res = template.render(**params)
        response = Response(str(res), content_type=ct)
        if not user_info:
            response.delete_cookie('beaker.session.id')
        return response

    # Entry Point
    def index(self, request, **params):
        raise HTTPBadRequest('not supported')

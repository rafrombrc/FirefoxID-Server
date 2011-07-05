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
from services.controllers import StandardController


class BaseController(StandardController):

    # used for unit testing only
    fake_session = {}

    def __init__(self, app):
        self.app = app

    def is_type(self, request, type_):
        """ Check if the request matches a given abbreviated content type """
        # type should be "html" or "json", but folks may request a full
        # content type. Be nice and trim it to the most likely correct
        # version.
        if "/" in type_:
            type_ = type_.split("/")[1]
        if ('output' in request.params and
            type_ == request.params.get('output', '')):
            return True
        try:
            return type_ in request.accept.header_value
        except AttributeError:
            # Header is not defined or present, so return "False" since it
            # can't match "nothing"
            return False

    def get_session_uid(self, request):
        if self.fake_session:
            return self.fake_session.get('uid', None)
        return request.environ.get('beaker.session', {}).get('uid')

    def set_session_uid(self, request, uid):
        if 'beaker.session' in request.environ:
            request.environ['beaker.session']['uid'] = uid
            return True
        return False

    def gen_signature(self, uid, request):
        """ Generate a signature value (to prevent XSS) """
        remote = request.remote_addr or 'localhost'
        sbs = (remote +
            self.app.config.get('auth.secret_salt', '') +
            str(uid))
        return sha1(sbs).hexdigest()

    def check_signature(self, uid, request):
        """ Check the enclosed signature """
        if 'sig' not in request.params:
            return False
        sig_val = request.params.get('sig', '')
        if len(sig_val) < 1:
            return False
        return sig_val != self.gen_signature(uid, request)

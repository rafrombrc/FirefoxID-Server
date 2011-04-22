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
# The Original Code is Sync Server
#
# The Initial Developer of the Original Code is the Mozilla Foundation.
# Portions created by the Initial Developer are Copyright (C) 2010
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#   Tarek Ziade (tarek@mozilla.com)
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
"""
Application entry point.
"""
from beaker.middleware import SessionMiddleware
from oidserver.auth import OIDAuthentication
from oidserver.controllers.auth import AuthController
from oidserver.controllers.oid import OIDController
from oidserver.storage import get_storage
from services.baseapp import set_app, SyncServerApp


urls = [
        #('GET', '/__debug__', 'svc', 'debug'),
        #('GET', '/__heartbeat__', 'svc', 'heartbeat'),
        ## private
        # Is the user Logged In?
        ('POST', '/1/logged_in', 'auth', 'logged_in'),
        # get the default email for this user
        ('POST', '/1/get_default_email', 'auth', 'get_default_email'),
        # get a list of emails for the given user (first is "default")
        ('POST', '/1/get_emails', 'auth', 'get_emails'),
        # remove the default email for this user
        ('POST', '/1/remove_association', 'auth', 'remove_association'),
        # get the identity assertion document.
        ('POST', '/1/get_identity_assertion', 'auth',
                'get_identity_assertion'),
        ('POST', '/1/authorize', 'auth', 'authorize'),
        ('POST', '/1/manage_info', 'auth', 'manage_info'),
        ('POST', '/1/manage_email', 'auth', 'manage_email'),
        # You're logged in, now authorize the email address
        ('GET', '/1/validate/{validate:[\w]+}', 'auth', 'validate'),
        ## public
        # verify that the identity assertion is valid.
        (('GET', 'POST'), '/1/login', 'auth', 'login'),
        # Log the user out of the system
        (('POST'), '/1/logout', 'auth', 'logout'),
        (('POST'), '/1/verify', 'auth', 'verify'),
        ('GET', '/{user:[@\w\.\-\+]+}', 'oid', 'get_user_info'),
        ]

controllers = {'oid': OIDController,
               'auth': AuthController}


class OIDApp(SyncServerApp):
    """OID application"""
    def __init__(self, urls, controllers, config, auth_class):
        """ Main storage """
        self.storage = get_storage(config, 'oidstorage')
        """ session cookie to uid (future)
                cookie should be "%id_hash+%rand(2**256)"
                * cookie valid for one login until the end of that session.
                * cookie is nuked at 'log out' or on expiration
                * New cookie on new session.
                * user has different cookies per machine or access.
        """
        #self.cookies = get_storage(config,'cookies')
        super(OIDApp, self).__init__(urls, controllers, config, auth_class)
        self.debug_page = '__debug__'


def _wrap(app):
    options = {'session.type': 'file',
               'session.data_dir': '/tmp/cache/data',
               'session.cookie_expires': True,
               'session.secure': True,
               'session.auto': True}
    return SessionMiddleware(app, options)


make_app = set_app(urls, controllers, klass=OIDApp, wrapper=_wrap,
                   auth_class=OIDAuthentication)

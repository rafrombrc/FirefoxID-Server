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
# The Original Code is Firefox Identity Server
#
# The Initial Developer of the Original Code is the Mozilla Foundation.
# Portions created by the Initial Developer are Copyright (C) 2011
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
from oidserver import VERSION
from oidserver.auth import OIDAuthentication
from oidserver.controllers.auth import AuthController
from oidserver.controllers.user import UserController
from oidserver.storage import get_storage
from services.baseapp import set_app, SyncServerApp


urls = [

        ## private
        # Is the user Logged In?
        ('POST', '/%s/authorize' % VERSION,
                'auth', 'authorize'),

        ## Main calls
        # Verify a given email address.
#        ('POST', '/%s/verify_address' % VERSION,
#                'auth', 'verify_address'),
        # (validate &) refresh a certificate that we have previously issued
#        (('GET', 'POST'), '/%s/refresh_certificate' % VERSION,
#                'auth', 'refresh_certificate'),
        # refresh a certificate by starting the dance over.
        ('GET', '/%s/refresh_certificate/{email:[^\/\?\&]+}' % VERSION,
                'auth', 'registered_emails'),
        # Alternate: no email means everything
        ('GET', '/%s/refresh_certificate' % VERSION,
                'auth', 'registered_emails'),
        # You're logged in, now authorize the email address via the token
        ('GET', '/%s/validate/{validate:[\w]+}' % VERSION,
                'auth', 'validate'),
        (('GET', 'POST'), '/%s/get_certificate' % VERSION,
                'auth', 'get_certificate'),
        ('GET', '/%s/random' % VERSION,
                'auth', 'random')
        ]

controllers = {'user': UserController,
               'auth': AuthController}


class OIDApp(SyncServerApp):
    """FirefoxID application"""

    def __init__(self, urls, controllers, config, auth_class):
#        import pdb; pdb.set_trace();
        if config.get('oid.admin_page', False):
                #Add the admin page functions.
                admin_urls = [
                        # admin page entry points.
                        ('POST', '/%s/manage_info' % VERSION,
                                'auth', 'manage_info'),
                        (('GET', 'POST'), '/%s/manage_email' % VERSION,
                                'auth', 'manage_email'),
                        (('GET', 'POST'), '/%s/login' % VERSION,
                                'auth', 'login'),
                        ('GET', '/%s/logged_in' % VERSION,
                                'auth', 'logged_in'),
                        # Log the user out of the system
                        (('GET', 'POST'), '/%s/logout' % VERSION,
                                'auth', 'logout'),
                        #(('POST'), '/%s/verify' % VERSION,
                        #        'auth', 'verify'),
                        ('GET', '/{user:[@\w\.\-\+]+}',
                                'user', 'get_user_info'),
                        ('GET', '/%s/register' % VERSION,
                                'auth', 'registered_emails')
                        ]
                # copy the admin_urls into the standard urls.
                map(urls.append, admin_urls)
        """ Main storage """
        self.storage = get_storage(config, 'oidstorage')
        super(OIDApp, self).__init__(urls, controllers, config, auth_class)
        # __heartbeat__ is provided via the SyncServerApp base class
        # __debug__ is provided via global.debug_page in config.


def _wrap(app, config = {}, **kw):
    # Beaker session config are defined in production.ini[default].
    # Pull the config settings from oidApp.config.
    # Defining custom config here summons dragons.
    return SessionMiddleware(app, config = config)

make_app = set_app(urls, controllers, klass=OIDApp, wrapper=_wrap,
                   auth_class=OIDAuthentication)

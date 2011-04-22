
from webob.exc import (HTTPBadRequest, HTTPTemporaryRedirect)
from webob import Response

from services.util import text_response, html_response, extract_username
from oidserver.util import (IdResMessage, check_authentication,
                            get_template, create_association)
from oidserver.controllers import BaseController

_OP_ROOT = 'https://services.mozilla.com/openid/'


class OIDController(BaseController):

    def get_user_info(self, request, **params):
        """ Display the appropriate user page or discovery page """
        user = str(request.sync_info['user'])
        params = {'user': user,
                  'host': self.app.config['oid.host'],
                  'login_host': self.app.config.get('oid.login_host',
                            'localhost')}

        if 'application/xrds+xml' in request.headers.get('Accept', ''):
            # Display the YADis discovery page
            template = get_template('yadis')
            ct = 'application/xrds+xml'
        else:
            uid = self.get_session_uid(request)
            if uid is not None:
                # Convert the user name to a standardized token
                user_name = extract_username(user)
                user_id = self.app.auth.backend.get_user_id(user_name)
                if user_id == uid:
                    # hey that's me !
                    user_info = self.app.storage.get_user_info(user_id)
                    print (user_info)
                    params['user_info'] = user_info
                    params['sig'] = self.gen_signature(uid, request)
                    params['sites'] = \
                            self.app.storage.get_associations_for_uid(user_id)
            # Use the older style of discovery (with link refs)
            template = get_template('user')
            ct = 'text/html'
        res = template.render(**params)
        return Response(str(res), content_type=ct)

    # Entry Point
    def index(self, request, **params):
        # getting the parameters
        redirect = request.environ['beaker.session'].get('redirect')
        if redirect is not None and params == {}:
            # fetch the parameters from the redirect (ignoring the first two
            # elements of the tuple)
            __, __, params = redirect
            del request.environ['beaker.session']['redirect']

        else:
            if request.method == 'POST':
                params = request.POST
            else:
                params = request.GET

        # distpatching the request depending on the mode
        if 'openid.mode' not in params:
            raise HTTPBadRequest('Missing "openid.mode"')

        mode = params.get('openid.mode')
        if mode == 'associate':
            return self.associate(params)

        # mandatory fields for other actions
        for field in ('openid.identity', ):
            if field not in params:
                raise HTTPBadRequest('Missing "%s"' % field)

        if mode == 'check_authentication':
            return self.check_authentication(params)
        elif mode in ('checkid_setup', 'checkid_immediate'):
            return self.checkid_setup(request, params)

        # other modes are ignored
        raise HTTPBadRequest('"%s" mode not supported' % mode)

    def associate(self, params):
        expires_in = self.app.config['oid.assoc_expires_in']
        res = create_association(self.app.storage, expires_in, **params)
        return text_response(res)

    def checkid_setup(self, request, params):

        # building the OpenId_Response message
        message = IdResMessage(self.app.storage, self.app.config['oid.host'],
                               self.app.config['oid.assoc_expires_in'],
                               **params)

        # signing it
        message.sign()

        # was it called by the identity plugin ?
        if 'X-Identity' in request.headers:
            # storing the site in allowed sites
            message.store_site()

            # redirecting
            raise HTTPTemporaryRedirect(location=message.get_url())
        else:
            # if not, we store the redirect url and display
            # a manual screen the user needs to validate
            token = message.store_redirect()
            template = get_template('check_setup')
            res = template.render(rely_party=message.site,
                                  identity=message.identity,
                                  token=token)
            return html_response(res)

    def checkid_submit(self, request, token):
        url, site, handle = self.app.storage.get_redirect(token)
        self.app.storage.add_site(handle, site)
        raise HTTPTemporaryRedirect(location=url)

    def check_authentication(self, params):
        res = check_authentication(self.app.storage, **params)
        return text_response(res)

    # crappy, temporary patch to get the special files in place.
    def blank(self, request, **params):
        ctype = {'html': 'text/html',
                 'css': 'text/css'}
        type = request.sync_info.get('ext', 'html')
        template = get_template('blank_' +
                                type)
        return Response(str(template.render(**params)),
                        content_type=ctype.get(type, 'text/html'))

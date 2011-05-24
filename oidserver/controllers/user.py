
from webob.exc import (HTTPBadRequest, HTTPTemporaryRedirect)
from webob import Response

from services.util import text_response, html_response, extract_username
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

        # other modes are ignored
        raise HTTPBadRequest('"%s" mode not supported' % mode)


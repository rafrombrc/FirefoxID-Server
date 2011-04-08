from hashlib import sha1, sha256
from oidserver import logger
from oidserver.controllers import BaseController
from oidserver.storage import OIDStorageException
from oidserver.util import get_template
from services.util import extract_username
from urllib import quote
from webob import Response
from webob.exc import HTTPBadRequest, HTTPFound

import base64
import hmac
import json
import time


class AuthException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class AuthController(BaseController):

    error_codes = {'LOGIN_ERROR': {'code': 401,
                                   'reason': ''},
                    'PARSE_ERROR': {'code': 400,
                                    'reason': ''},
                    'INVALID': {'code': 403,
                                'reason': ''},
                    'ID_NOT_SELECTED': {'code': 412,
                                    'reason': ''},
                    'NOT_FOUND': {'code': 404,
                                  'reason': ''}
    }

    def get_template_from_request(self, request):
        if self.is_type(request, 'json'):
            template = get_template('json_response')
            content_type = 'application/json'
        else:
            template = get_template('html_response')
            content_type = 'text/html'
        return (content_type, template)

    #Responses
    def logged_in(self, request, **kw):
        logged_in = False
        (content_type, template) = self.get_template_from_request(request)
        uid = self.get_uid(request)
        if uid is not None:
            logged_in = True
            assoc_handle = self.app.storage.get_assoc_handle(uid, request)
            try:
                association = self.app.storage.get_association(assoc_handle)
                if association:
                    logged_in = association.get('state',True)
            except OIDStorageException:
                pass
        if logged_in:
            body = template.render(response = {'success': True,
                                            'logged_in': True,
                                            },
                                       request = request
                                       )
        else:
            body = template.render(error=
                                       self.error_codes.get('LOGIN_ERROR'),
                                       request = request)
        return Response(str(body), content_type=content_type)

    def get_default_email(self, request, **kw):
        """return the default email
        """
        (content_type, template) = self.get_template_from_request(request)
        uid = self.get_uid(request)
        if uid is None:
            body = template.render(request = request,
                                       error =
                                       self.error_codes.get('LOGIN_ERROR'))
        else:
            ## first to see if the user has an association
            assoc_handle = self.app.storage.get_assoc_handle(uid, request)
            association = self.app.storage.get_association(assoc_handle)
            if (association is None or
                association.get('state', False) is False or
                association.get('email') is None):
                body = template.render(
                        request = request,
                        config = self.app.config,
                        error =
                         self.error_codes.get('LOGIN_ERROR'))
            else:
                iar = self.gen_identity_assertion(request)
                body = template.render(request = request,
                            config = self.app.config,
                            response = {'email': association.get('email'),
                                        'iar': iar})
        return Response(str(body), content_type = content_type)

    def get_emails(self, request, **kw):
        """return the default email
        """
        body = ''
        (content_type, template) = self.get_template_from_request(request)
        uid = self.get_uid(request)
        if uid is None:
            body = template.render(error =
                                       self.error_codes.get('LOGIN_ERROR'),
                                       request = request,
                                       config = self.app.config
                                        )
        else:
            ## first to see if the user has an association
            assoc_handle = self.app.storage.get_assoc_handle(uid, request)
            emails = self.app.storage.get_emails(uid, assoc_handle)
            emails['iar'] = self.gen_identity_assertion(request)
            body = template.render(response = emails,
                                       request = request,
                                       config = self.app.config)
        return Response(str(body), content_type = content_type)

    def remove_association(self, request, **kw):
        (content_type, template) = self.get_template_from_request(request)
        # Check crumb !!
        uid = self.get_uid(request, strict=False)
        site = request.params.get('site_id', None)
        handle = self.app.storage.get_assoc_handle(uid,
                                                   request,
                                                   site_loc = site)
        if uid is None:
            body = template.render(error =
                                       self.error_codes.get('LOGIN_ERROR'),
                                       config = self.app.config,
                                       request = request)
        else:
            if self.app.storage.del_association(handle):
                body = template.render(request = request,
                                           config = self.app.config)
            else:
                body = template.render(request = request,
                                config = self.app.config,
                                error = self.error_codes.get('NOT_FOUND'))
        return Response(str(body), content_type = content_type)

    def get_identity_assertion(self, request, **kw):
        body = ''
        (content_type, template) = self.get_template_from_request(request)
        iar = self.gen_identity_assertion(request)
        if iar is None:
            body = template.render(request = request,
                                config = self.app.config,
                                error = self.error_codes.get('LOGIN_ERROR'))
        else:
            body = template.render(request = request,
                                       response = {'iar': iar},
                                       config = self.app.config)
        return Response(str(body), content_type = content_type)

    def verify(self, request, **kw):
        body = ''
        (content_type, template) = self.get_template_from_request(request)
        uid = self.get_uid(request)
        user = None
        if uid is not None:
            user = self.app.storage.get_user_info(uid)
        if uid is None or user is None:
            body = template.render(
                                request = request,
                                config = self.app.config,
                                error = self.error_codes.get('LOGIN_ERROR'))
        else:
            if not self.validate_json_web_token(request.params.get('iar', '')):
                body = template.render(
                                        request = request,
                                        config = self.app.config,
                                        error =
                                           self.error_codes.get('INVALID'))
            else:
                body = template.render(request = request,
                                           config = self.app.config)
        return Response(str(body), content_type = content_type)

    def authorize(self, request):
        body = ''
        (content_type, template) = self.get_template_from_request(request)
        # Override the default if this is an HTML request.
        if 'html' in content_type:
            template = get_template('authorize')
        uid = request.environ.get('beaker.session', {}).get('logged_in', None)
        if uid is None:
            return self.login(request)
        user = self.app.storage.get_user_info(uid)
        target_email = request.params.get('temail', None)
        #verify that this is one of the user's valid emails.
        if target_email not in user.get('emails'):
            target_email = None
        if target_email is not None:
            # Set the association
            assoc_handle = self.app.storage.get_assoc_handle(uid, request)
            site_id = self.app.storage.gen_site_id(request)
            if not site_id:
                body = template.render(
                        request = request,
                        config = self.app.config,
                        error = self.error_codes.get('INVALID'))
                return Response(str(body), content_type = content_type)
            site_secret = self.app.storage.gen_site_secret(request,
                        site_id,
                        salt = self.app.config.get('site.secret_salt', ''))
            association = self.app.storage.set_association(uid, request,
                                        handle = assoc_handle,
                                        secret = site_secret,
                                        site_id = site_id,
                                        email = target_email,
                                        state = True
                                        )
            #We're done here, return the POSTMESSAGE trigger
            (content_type, template) = self.get_template_from_request(request)
            # force the path to be "login" for the operation.
            body = template.render(response = {
                'id': association.get('site_id'),
                'secret': association.get('secret')},
                operation = 'login',
                request = request)
        else:
            # No email picked, present the listatp
            body = template.render(response = {'user': user},
                                       request = request)
        return Response(str(body), content_type = content_type)

    def login(self, request, **kw):
        response = {}
        error = {}
        clear_login = False;
        (content_type, template) = self.get_template_from_request(request)
        # User is not logged in or the association is not present.
        if (len(request.POST.get('email', '')) and
            len(request.POST.get('password', ''))):
            email = request.POST['email']
            password = request.POST['password']
            # Remove the cookie (if present)
            clear_login = True;
            try:
                username = extract_username(email)
            except UnicodeError:
                # Log the invalid username for diagnostics ()
                logger.warn('Invalid username specified: %s (%s) '
                            % (email, username))
                raise HTTPBadRequest()
            # user normalization complete, check to see if we know this
            # person
            uid = self.app.auth.backend.authenticate_user(username,
                                                          password)
            if uid is not None:
                # User is valid, record the association
                storage = self.app.storage
                request.environ['beaker.session']['logged_in'] = uid
                clear_login = False;
                if not storage.gen_site_id(request):
                    # HTTPTemporaryRedirect = 307
                    # HTTPFound  = 302 // does not pass args.
                    raise HTTPFound(location = "/%s" %
                                                quote(email))
                assoc_handle = storage.get_assoc_handle(uid, request)
                association = storage.get_association(assoc_handle)
                user = storage.get_user_info(uid)
                if user is None:
                    # Record the user
                    user = storage.set_user_info(uid, email,
                                                 emails = [email, ]
                                                 )
                if association is None or not association.get('state',True):
                    if (self.is_type(request,'html')):
                        return self.authorize(request)
                    else:
                        error = self.error_codes.get('LOGIN_ERROR')
                else:
                    # All is well, respond successfully
                    response = {
                        'id': association.get('site_id'),
                        'secret': association.get('secret')
                        }
                    body = template.render(response = response,
                                            request = request,
                                            config = self.app.config)
                    return Response(str(body), content_type = content_type)
            else:
                # failed
                logger.debug("Login failed for %s " % email)
                error = self.error_codes.get('LOGIN_ERROR')
        else:  # test if uid is present in cookie.
            uid = self.get_uid(request)
            if uid is not None:
                return self.authorize(request)
        # Display the login page for HTML only
        if self.is_type(request, 'html'):
            template = get_template('login')
        body = template.render(error = error,
                                   response = response,
                                   config = self.app.config,
                                   request = request)
        resp = Response(str(body), content_type = content_type)
        if clear_login:
            resp.delete_cookie('beaker.session.id')
        return resp

    def logout(self, request, **kw):
        # sanitize value (since this will be echoed back)
        (content_type, template) = self.get_template_from_request(request)
        body = {}
        if 'html' in content_type:
            template = get_template('login')
        uid = self.get_uid(request)
        if uid is None:
                body = template.render(error =
                                        self.error_codes.get('LOGIN_ERROR'),
                                        config = self.app.config,
                                        request = request)
        else:
            # This is potentially dangerous, check that this is at least
            # semi-legit
            if not self.check_signature(uid, request):
                raise HTTPBadRequest()
            assoc_handle = self.app.storage.get_assoc_handle(uid, request)
            if not self.app.storage.set_assoc_state(assoc_handle, False):
                logger.warn("Could not deactivate association")
        request.environ['beaker.session'].delete()
        resp = Response(str(body), content_type = content_type)
        resp.delete_cookie('beaker.session.id')
        return resp

    #Utils
    def as_json_web_token(self, payload):
        server_secret = self.app.config.get('auth.server_secret', '')
        header = {"typ": "JWT", "alg": "HS256"}
        b64_headers = base64.b64encode(json.dumps(header))
        b64_payloads = base64.b64encode(json.dumps(payload))
        sig_base_string = "%s.%s" % (b64_headers, b64_payloads)
        signature = hmac.new(server_secret, sig_base_string, sha256).digest()
        b64_sig = base64.b64encode(signature)
        return "%s.%s.%s" % (b64_headers, b64_payloads, b64_sig)

    def validate_json_web_token(self, token):
        if token is None or len(token) == 0:
            return False
        (header, payload, sig) = token.split('.')
        server_secret = self.app.config.get('auth.server_secret', '')
        sig_base_string = "%s.%s" % (header, payload)
        signature = hmac.new(server_secret, sig_base_string, sha256).digest()
        b64_sig = base64.b64encode(signature)
        return b64_sig == sig

    def check_signature(self, uid, request):
        """ Check the enclosed signature """
        if 'sig' not in request.params:
            return False
        sig_val = request.params.get('sig', '')
        if len(sig_val) < 1:
            return False
        return sig_val != self.gen_signature(uid, request)

    def isAssociationValid(self, uid, request):
        assoc_record = self.app.storage.get_association(
                self.app.storage.get_assoc_handle(uid, request))
        if assoc_record is None:
            return False
        return assoc_record.get('state', True)

    def gen_identity_assertion(self, request):
        """return the default email
        """
        (content_type, template) = self.get_template_from_request(request)
        uid = self.get_uid(request)
        user = None
        if uid is not None:
            user = self.app.storage.get_user_info(uid)
        #if the user is none, should we establish an association?
        if user is not None:
            valid_period = self.app.config.get('auth.valid_until', 300)
            valid_until = int(time.time()) + valid_period
            identity_assertion = {
                'type': 'server-signed',
                'issuer': self.app.config.get('auth.issuer', 'untrusted'),
                'audience': request.host,
                'valid-until': valid_until,
                'email': user.get('email')
            }
            return self.as_json_web_token(identity_assertion)
        return None

    def gen_signature(self, uid, request):
        """ Generate a signature value (to prevent XSS) """
        sbs = (request.remote_addr +
            self.app.config.get('auth.secret_salt', '') +
            str(uid))
        return sha1(sbs).hexdigest()

    def get_uid(self, request, strict=True, **kw):
        ## currently pull this from the cookie.
        uid = None
        if 'email' in request.params:
            assoc_record = self.app.storage.get_association_by_email(request,
                                                request.params.get('email'))
            if assoc_record is not None:
                return assoc_record.get('uid', None)
        try:
            uid = request.environ['beaker.session']['logged_in']
            # Check the assoc_record to see if this association is still valid
            if strict and not self.isAssociationValid(uid, request):
                return None
        except KeyError:
            pass
        return uid

from hashlib import  sha256
from oidserver import logger, VERSION
from oidserver.controllers import BaseController
from oidserver.storage import OIDStorageException
from oidserver.util import (get_template, text_to_html_filter, url_filter)
from services.util import extract_username
from time import time
from urllib import quote, unquote
from webob import Response
from webob.exc import HTTPBadRequest, HTTPFound, HTTPForbidden

import base64
import hmac
import json
import smtplib


class AuthException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class AuthController(BaseController):

    ## db: uid: emails{ email:{state: (verified, pending), created}

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

    ## public
    def refresh_certificate(self, request, **kw):
        """ Refresh a given's certificate """
        error = None
        response = None
        (content_type, template) = self.get_template_from_request(request)
        uid = self.get_session_uid(request)
        pub_key = request.params.get('pubkey')
        if pub_key is None:
            logger.warn("Request missing pubkey argument")
            raise HTTPBadRequest()
        cert_info = self.parse_certificate(uid, request)
        if cert_info is None:
            raise HTTPBadRequest()
        (state, address_info) = self.check_cert(uid, cert_info)
        if not state:
            raise HTTPBadRequest()
        try:
            response = self.gen_certificate(address_info.get('email'),
                                            request.params.get('pubkey'))
        except OIDStorageException, ose:
            error = self.error_codes.get('INVALID')
            error.reason = str(ose)
        body = template.render(request = request,
                               config = self.app.config,
                               error = error,
                               response = response)
        return Response(str(body), content_type = content_type)

    # called during connection. invokes naviator.id.registerVerfiedEmail(email)
    def registered_emails(self, request, **kw):
        response = None
        error = None
        uid = self.get_session_uid(request)
        (content_type, template) = self.get_template_from_request(request,
                                                    html_template = "register")
        if uid is None:
            error = self.error_codes.get('LOGIN_ERROR')
        else:
            user_info = self.app.storage.get_user_info(uid)
            emails = []
            for email in user_info.get('emails'):
                email_record = user_info['emails'].get(email)
                if email_record.get('state',None) == 'verified':
                    emails.append(email)
            response = {'emails': emails}
        body = template.render(request = request,
                               config = self.app.config,
                               error = error,
                               callback = 'navigator.id.registerVerifiedEmail',
                               response = response)
        return Response(str(body), content_type = content_type)

    def gen_callback_url(self, uid, email):
        ### TODO
        return 'TODO'

    def gen_certificate(self, email, ua_pub_key):
        ttl = time() + self.app.config.get('auth.cert_ttl_in_secs', 86400)
        certificate_info = {
            'id': email,
            'valid-until': ttl,
            'issuer': self.app.config.get('auth.issuer', 'UNDEFINED'),
            'publicKey': ua_pub_key
        }
        return self.as_json_web_token(certificate_info)

    def get_certificate(self, request, **kw):
        response = None
        error = None
        (content_type, template) = self.get_template_from_request(request,
                                        html_template = 'register_cert')
        pub_key = request.params.get('pubkey',None)
        email = request.params.get('id',None)
        uid = self.get_session_uid(request)
        if email is None or pub_key is None:
            logger.warn('get_cerficate is missing required data')
            error = self.error_codes.get('INVALID')
        elif email not in self.app.storage.get_addresses(uid, 'verified'):
            logger.warn('get_certificate passed an unverified email')
            error = self.error_codes.get('INVALID')
        else:
            response = {'certificate': self.gen_certificate(email,
                                                          pub_key),
                        'callbackUrl': self.gen_callback_url(uid, email)}
        body = template.render(request = request,
                    response = response,
                    config = self.app.config,
                    error = error,
                    callback = "navigator.id.registerVerifiedEmailCertificate")
        return Response(str(body), content_type = content_type)

    def verify(self, request, **kw):
        """ Verify an IAR.
        """
        body = ''
        (content_type, template) = self.get_template_from_request(request)
        if not self.validate_json_web_token(request.params.get('iar', '')):
            body = template.render(
                request = request,
                config = self.app.config,
                error = self.error_codes.get('INVALID'))
        else:
            body = template.render(request = request,
                                   config = self.app.config)
        return Response(str(body), content_type = content_type)

    # Admin Calls
    def logged_in(self, request, **kw):
        if not self.is_internal(request):
            raise HTTPForbidden()
        logged_in = False
        (content_type, template) = self.get_template_from_request(request)
        uid = self.get_uid(request)
        if uid is not None:
            logged_in = True
            """
            assoc_handle = self.app.storage.get_assoc_handle(uid, request)
            try:
                association = self.app.storage.get_association(assoc_handle)
                if association:
                    logged_in = association.get('state', True)
            except OIDStorageException:
                pass
            #"""
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
        return Response(str(body), content_type = content_type)

    def login(self, request, extra = {}, **kw):
        """ Log a user into the ID server
        """
        response = {}
        error = {}
        uid = None
        email = None
        storage = self.app.storage

        (content_type, template) = self.get_template_from_request(request,
                                                    html_template = 'login')
        # User is not logged in or the association is not present.
        if (len(request.POST.get('id', '')) and
            len(request.POST.get('password', ''))):
            email = request.POST['id']
            password = request.POST['password']
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
            if uid is None:
                error = self.error_codes.get('LOGIN_ERROR')
                logger.debug('Login failed for %s ' % email)
                body = template.render(error = error,
                                       response = response,
                                       extra = extra,
                                       request = request,
                                       config = self.app.config)
                response = Response(str(body), content_type = content_type)
                logger.debug('Nuking session cookie')
                response.delete_cookie('beaker.session.uid')
                try:
                    del request.environ['beaker.session']['uid']
                except KeyError:
                    pass
                return response
            logger.debug('setting uid to %s' % uid)
            request.environ['beaker.session']['uid'] = uid

            # if this is an email validation, skip to that.
            if 'validate' in request.params:
                return self.validate(request)
        # Attempt to get the uid.
        if uid is None:
            logger.debug('attempting to get uid')
            uid = self.get_uid(request, strict = False)
            if uid is None:
                logger.debug('no uid present')
                # Presume that this is the first time in.
                # Display the login page for HTML only
                body = template.render(error = error,
                                        response = response,
                                        config = self.app.config,
                                        extra = extra,
                                        request = request)
                response = Response(str(body), content_type = content_type)
                response.delete_cookie('beaker.session.uid')
                return response
        # Ok, got a UID, so let's get the user info
        user = storage.get_user_info(uid)
        if not email:
            email = request.params.get('email', None)
            if email:
                self.send_validate_email(uid, email)
        logger.debug('Sending user to admin page')
        raise HTTPFound(location = "https:/%s" % quote(email))

    def logout(self, request, **kw):
        """ Log a user out of the ID server
        """
        # sanitize value (since this will be echoed back)
        logger.debug('Logging out.')
        (content_type, template) = self.get_template_from_request(request,
                                                    html_template = 'login')
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
        body = template.render(response = True,
                               request = request,
                               config = self.app.config)
        response = Response(str(body), content_type = content_type)
        return response

    def manage_email(self, request, **kw):
        (content_type, template) = self.get_template_from_request(request,
                                    html_template = 'confirm_email_notice')
        uid = self.get_uid(request, strict = False)
        if not uid:
            return HTTPBadRequest()
        if 'unv' in request.params and 'act' in request.params:
            email = request.params.get('unv')
            if '@' not in email:
                email = unquote(email)
            action = request.params.get('act').lower()
            user = self.app.storage.get_user_info(uid)
            if action == 'add':
                if self.send_validate_email(uid, email):
                    body = template.render(request = request,
                                           config = self.app.config,
                                           user = user,
                                           email = email)
                    return Response(str(body),
                                    content_type = content_type)
            elif action == 'del':
                if not self.app.storage.remove_unvalidated(uid, email):
                    body = template.render(request = request,
                                    config = self.app.config,
                                    email = email,
                                    user = user,
                                    error = self.error_codes('INVALID'))
                else:
                    body = template.render(request = request,
                                    config = self.app.config,
                                    user = user,
                                    email = email)
                return Response(str(body), content_type = content_type)
            return HTTPBadRequest()
        user_info = self.app.storage.get_user_info(uid)
        raise HTTPFound(location = "https:/%s/%s" %
                (self.app.config.get('oid.login_host', 'https://localhost'),
                         quote(user_info.get('pemail'))))

    def send_validate_email(self, uid, email, nosend = False, **kw):
        """ Send an email containing the validation token URL to the
            newly registered email, and add the email to the list of
            unvalidated emails.
        """
        #first, generate a token:
        user = self.app.storage.get_user_info(uid)
        if user is None:
            return False
        mailserv_name = self.app.config.get('oid.mail_server',
                                                  'localhost')
        reply_to = self.app.config.get('oid.reply_to',
                                       'no-reply@' + mailserv_name)
        #store the unverified email
        unv_emails = user.get('unv_emails', {})
        if (email not in unv_emails):
            rtoken = self.app.storage.add_validation(uid, email)
        else:
            rtoken = self.app.storage.get_validation_token(uid, email)
        # format the email and send it on it's merry way.
        template = get_template('validate_email_body')
        verify_url = (self.app.config.get('oid.validate_host',
                                         'http://localhost') +
                                        '/%s/validate/%s' % (VERSION, rtoken))
        body = template.render(from_addr =
                                self.app.config.get('oid.from_address',
                                                    reply_to),
                               to_addr = email,
                               reply_to = reply_to,
                               verify_url = verify_url)
        if (not nosend and not self.app.config.get('test.nomail', False)):
            #for testing, we don't send out the email. (Presume that works.)
            logger.debug('sending validation email to %s' % email)
            server = smtplib.SMTP(mailserv_name)
            server.sendmail(reply_to,
                            email,
                            body)
            server.quit()
        return True

    def validate(self, request, **kw):
        """ Validate a user email token
        """
        (content_type, tempate) = self.get_template_from_request(request)
        token = request.sync_info.get('validate',
                                      request.params.get('validate',
                                                         None))
        if token is None:
            raise HTTPBadRequest()
        uid = self.get_uid(request, strict = False)
        if not uid:
            extra = {}
            extra['validate'] = token
            return self.login(request, extra)
        body = ""
        try:
            email = self.app.storage.check_validation(uid, token)
        except OIDStorageException:
            raise HTTPBadRequest()
        if not email:
            raise HTTPBadRequest()
        template = get_template('validation_confirm')
        user = self.app.storage.get_user_info(uid)
        body = template.render(request = request,
                               user = user,
                               email = email,
                               config = self.app.config)
        return Response(str(body), content_type = 'text/html')

    def verify_address(self, request, **kw):
        """ Verify a given address """
        ## Only logged in users can play
        uid = self.get_session_uid(request)
        if uid is None:
            raise HTTPForbidden()
        email = request.params.get('id', None)
        if email is None:
            raise HTTPBadRequest()
        (content_type, template) = self.get_template_from_request(request,
                                            html_template = 'send_verify')
        address_info = self.app.storage.get_address_info(email)
        if address_info is None:
            body = template.render(error = self.error_codes.get('LOGIN_ERROR'))
        else:
            if address_info.get('uid', None) != uid:
                body = template.render(error =
                                       self.error_codes.get('LOGIN_ERROR'))
            else:
                state = address_info.get('state',None)
                if state == 'verified':
                    return self.generate_assertion(email, request)
                elif address_state == 'pending' or address_state == 'needs validation':
                    self.send_validate_email(uid, email)
                    body = template.render(response = {'success': True,
                                               'status': 'sending',
                                               'id': email})
                else:
                    raise HTTPForbidden()
        return Response(str(body), content_type = content_type)

    #Utils
    def as_json_web_token(self, payload):
        """ Convert a payload object into a JWT
        """
        server_secret = self.app.config.get('auth.server_secret', '')
        header = {"typ": "JWT", "alg": "HS256"}
        b64_headers = base64.b64encode(json.dumps(header))
        b64_payloads = base64.b64encode(json.dumps(payload))
        sig_base_string = "%s.%s" % (b64_headers, b64_payloads)
        signature = hmac.new(server_secret, sig_base_string, sha256).digest()
        b64_sig = base64.b64encode(signature)
        return "%s.%s.%s" % (b64_headers, b64_payloads, b64_sig)

    def parse_certificate(self, uid, request, acceptible = None, **kw):
        certificate = request.params.get('certificate', None)
        if certificate is None:
            logger.error("No certificate found for refresh")
            raise None
        return self.from_json_web_token(certificate)

    def check_cert(self, uid, cert_info, acceptible = None):
        address_info = None
        if 'id' not in cert_info:
            logger.error("No email address found in certificate")
            return (False, address_info)
        address_info = \
            self.app.storage.get_address_info(uid, cert_info.get('id'))
        if address_info is None:
            logger.warn("No address info for certificate id %s, uid: %s " %
                        (cert_info.get('id'), uid))
            return (False, address_info)
        if acceptible is None:
            acceptible = ('verified')
        if address_info.get('state', None) not in acceptible:
            logger.warn("Email address is not in acceptible states %s.",
                        acceptible)
            return (False, address_info)
        return (True, address_info)

    def from_json_web_token(self, jwt):
        """ Convert a JWT to a payload
        """
        server_secret = self.app.config.get('auth.server_secret','')
        (jhead, jbody, jsig) = jwt.split('.');
        header = json.loads(base64.b64decode(jhead))
        if str(header['alg']).upper() != "HS256":
            raise AuthException("Unrecognized JWT encoding. Please use HS256")
        sig_base_string = "%s.%s" % (jhead, jbody)
        signature = base64.b64encode(hmac.new(server_secret,
                                              sig_base_string,
                                              sha256).digest())
        if signature != jsig:
            logger.error("JWT has invalid signature. Aborting.")
            raise AuthException("Invalid JWT signature.")
        return json.loads(base64.b64decode(jbody))


    def gen_identity_assertion(self, request, data=None):
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
            valid_until = int(time()) + valid_period
            identity_assertion = {
                'type': 'server-signed',
                'issuer': self.app.config.get('auth.issuer', 'untrusted'),
                'audience': request.host,
                'valid-until': valid_until,
                'id': user.get('email')
            }
            if data is not None:
                identity_assertion['data'] = data
            return self.as_json_web_token(identity_assertion)
        return None

    def get_template_from_request(self, request,
                                  html_template = 'html_response',
                                  **kw):
        if self.is_type(request, 'json'):
            template = get_template('json_response')
            content_type = 'application/json'
        else:
            template = get_template(html_template)
            content_type = 'text/html'
        return (content_type, template)

    def get_uid(self, request, strict = True, **kw):
        uid = None
        try:
            uid = self.get_session_uid(request)
        except KeyError:
            pass
        return uid

    def is_internal(self, request):
        # placeholder function for internal only calls.
        return True

    def validate_json_web_token(self, token):
        """ Confirm that the given JWT is a properly specified object
            originating from this domain.
        """
        if token is None or len(token) == 0:
            return False
        (header, payload, sig) = token.split('.')
        server_secret = self.app.config.get('auth.server_secret', '')
        sig_base_string = "%s.%s" % (header, payload)
        signature = hmac.new(server_secret, sig_base_string, sha256).digest()
        b64_sig = base64.b64encode(signature)
        return b64_sig == sig

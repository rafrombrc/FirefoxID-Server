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
from oidserver import logger, VERSION
from oidserver.controllers import BaseController
from oidserver.jws import JWS, JWSException
from oidserver.storage import OIDStorageException
from oidserver.util import (get_template)
from Crypto.Random import random
from services.util import extract_username
from time import time
from urllib import quote, unquote
from webob import Response
from webob.exc import HTTPBadRequest, HTTPFound, HTTPForbidden

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
        jws = JWS(config = self.app.config)
        error = None
        response = None
        (content_type, template) = self.get_template_from_request(request)
        uid = self.get_session_uid(request)
        pub_key = request.params.get('pubkey')
        if pub_key is None:
            logger.warn("Request missing pubkey argument")
            raise HTTPBadRequest()
        try:
            cert_info = jws.parse(request.params.get('certificate', None))
            if cert_info is None:
                logger.error('Certificat information missing from request')
                raise HTTPBadRequest()
        except JWSException, ex:
            logger.error('Could not parse JWS object: %s ' % str(ex))
            raise HTTPBadRequest()
        (state, address_info) = self.check_cert(uid, cert_info)
        if not state:
            raise HTTPBadRequest()
        try:
            response = {'certificate': self.gen_certificate(
                        address_info.get('email'),
                        request.params.get('pubkey')),
                        'callbackUrl': self.gen_callback_url(uid,
                                                cert_info.get('id'))}
        except OIDStorageException, ose:
            error = self.error_codes.get('INVALID')
            error.reason = str(ose)
        body = template.render(request = request,
                               config = self.app.config,
                               error = error,
                               response = response)
        return Response(str(body), content_type = content_type)

    # called during connection. invokes
    # navigator.id.registerVerifiedEmail(email)
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
            candidates = []
            emails = []
            pref_email = request.params.get('email', None)
            if pref_email:
                if pref_email in user_info.get('emails'):
                    candidates.append(pref_email)
            else:
                candidates = user_info.get('emails')
            for email in candidates:
                email_record = user_info['emails'].get(email)
                if email_record.get('state', None) == 'verified':
                    emails.append(email)
            response = {'emails': emails}
        body = template.render(request = request,
                            config = self.app.config,
                            error = error,
                            callback = 'navigator.id.registerVerifiedEmails',
                            response = response)
        return Response(str(body), content_type = content_type)

    def gen_callback_url(self, uid, email):
        return "%s/%s/%s" % (self.app.config.get('oid.login_host',
                                                  'localhost'),
                          'refresh_certificate',
                          quote(email))

    def gen_certificate(self, email, ua_pub_key):
        ttl = time() + self.app.config.get('auth.cert_ttl_in_secs', 86400)
        certificate_info = {
            'id': email,
            'valid-until': ttl,
            'issuer': self.app.config.get('auth.issuer', 'UNDEFINED'),
            'publicKey': ua_pub_key
        }
        jws = JWS(config = self.app.config)
        return jws.sign(certificate_info)

    def get_certificate(self, request, **kw):
        response = None
        error = None
        (content_type, template) = self.get_template_from_request(request,
                                        html_template = 'register_cert')
        pub_key = request.params.get('pubkey', None)
        email = request.params.get('id', None)
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

    def random(self, request, **kw):
        """ Return a random number
        """
        rset = []
        for i in range(16):
            rset.append(random.getrandbits(256))
        (content_type, template) = self.get_template_from_request(request)
        body = template.render(request = request,
                               response = {'random': rset},
                               config = self.app.config
                               )
        return Response(str(body), content_type = content_type)

    def verify(self, request, **kw):
        """ Verify an IAR.
        """
        body = ''
        jws = JWS(config = self.app.config)
        (content_type, template) = self.get_template_from_request(request)
        if not jws.verify(request.params.get('iar', '')):
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

        if not self.is_internal(request):
            raise HTTPForbidden()
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
        if not email:
            email = request.params.get('id', None)
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
        if user is None:
            user = storage.create_user(uid, email)
        if email:
            if email not in user.get('emails', []):
                self.send_validate_email(uid, email)
            if (len(request.params.get('audience', ''))):
                return self.registered_emails(request)
            location = "%s/%s" % (self.app.config.get('oid.login_host',
                                                          'localhost'),
                 quote(email))
        else:
            del (request.environ['beaker.session']['uid'])
            location = "%s/%s/login" % (self.app.config.get('oid.login_host',
                                                            'localhost'),
                                        VERSION)
        logger.debug('Sending user to admin page %s' % location)
        raise HTTPFound(location = location)

    def logout(self, request, **kw):
        """ Log a user out of the ID server
        """
        # sanitize value (since this will be echoed back)
        if not self.is_internal(request):
            raise HTTPForbidden()
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
        if not self.is_internal(request):
            raise HTTPForbidden()
        uid = self.get_uid(request, strict = False)
        email = request.params.get('email', '')
        if not uid:
            logger.warn("Invalid request, no uid")
            return HTTPBadRequest()
        if not email:
            logger.warn("Malformed, manage request, no email")
            return HTTPBadRequest()
        if 'act' in request.params:
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
                type = request.params.get('type', None)
                error = False
                if not type:
                    logger.warn("Malformed, missing type")
                    return HTTPBadRequest()
                if type.lower() == 'unv':
                    if not self.app.storage.remove_email(uid,
                                                         email = email,
                                                         state = 'pending'):
                        error = True
                elif type.lower() == 'reg':
                    #For now, don't allow users to remove their verified
                    # primary email
                    if email.lower() == user.get('primary', '').lower():
                        return HTTPBadRequest()
                    if not self.app.storage.remove_email(uid,
                                                         email = email,
                                                         state = 'verified'):
                        error = True
                if error:
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
        raise HTTPFound(location = "%s/%s" %
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
            logger.error('No validation token discovered in request')
            raise HTTPBadRequest()
        uid = self.get_uid(request, strict = False)
        if not uid:
            extra = {'validate': token}
            return self.login(request, extra)
        body = ""
        try:
            email = self.app.storage.check_validation(uid, token)
        except OIDStorageException, ex:
            logger.error('Could not check token for user %s, %s' %
                         (uid, str(ex)))
            raise HTTPBadRequest()
        if not email:
            logger.error('No email associated with uid:%s and token:% ' %
                         (uid, token))
            raise HTTPBadRequest()
        template = get_template('validation_confirm')
        user = self.app.storage.get_user_info(uid)
        body = template.render(request = request,
                               user = user,
                               email = email,
                               config = self.app.config)
        return Response(str(body), content_type = 'text/html')

    def verify_address(self, request, **kw):
        """ Verify a given address (unused?)
        """
        if not self.is_internal(request):
            raise HTTPForbidden()
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
                address_state = address_info.get('state', None)

                if address_state == 'verified':
                    return self.generate_assertion(email, request)
                elif (address_state == 'pending' or
                      address_state == 'needs validation'):
                    self.send_validate_email(uid, email)
                    body = template.render(response = {'success': True,
                                               'status': 'sending',
                                               'id': email})
                else:
                    raise HTTPForbidden()
        return Response(str(body), content_type = content_type)

    #Utils
    def check_cert(self, uid, cert_info, acceptible = None):
        address_info = None
        if 'id' not in cert_info:
            logger.error("No email address found in certificate")
            return (False, address_info)
        address_info = self.app.storage.get_address_info(uid,
                                                         cert_info.get('id'))
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
            if not self.app.storage.check_user(uid):
                return None
        except KeyError:
            pass
        return uid

    def is_internal(self, request):
        # placeholder function for internal only calls.
        return True

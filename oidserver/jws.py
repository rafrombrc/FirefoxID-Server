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
from M2Crypto import RSA, BIO, ASN1
from hashlib import sha256, sha384, sha512
from oidserver import logger

import base64
import hmac
import cjson


class JWSException (Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class JWS:
    _header = None      # header information
    _crypto = None      # usually the signature
    _claim = None       # the payload of the JWS
    _config = {}        # App specific configuration values


    def __init__(self, config = None, **kw):
        if config:
            self._config = config
        else:
            config = {}
        self._sign = {'HS': self._sign_HS,
                 'RS': self._sign_RS,
                 'NO':  self._sign_NONE}
        self._verify = {'HS': self._verify_HS,
                   'RS': self._verify_RS,
                   'NO':  self._verify_NONE}

    def sign(self, payload, header = None, alg = None, **kw):
        if payload is None:
            raise (JWSException("Cannot encode empty payload"))
        header = self.header(alg = alg)
        if alg is None:
            alg = header.get('alg', 'NONE')
        try:
            signer = self._sign.get(alg[:2].upper())
        except KeyError, ex:
            logger.error("Invalid JWS Sign method specified %s", str(ex))
            raise(JWSException("Unsupported encoding method specified"))
        header_str = base64.urlsafe_b64encode(cjson.encode(header))
        payload_str = base64.urlsafe_b64encode(cjson.encode(payload))
        sbs = "%s.%s" % (header_str, payload_str)
        signed = signer(alg, header, sbs)
        if signed:
            return signed
        else:
            return sbs

    def parse(self, jws, **kw):
        if not jws:
            raise(JWSException("Cannot verify empty JWS"))
        if self.verify(jws):
            (head, payload_str, signature) = jws.split('.')
            payload = cjson.decode(base64.b64decode(payload_str))
            return payload
        else:
            raise(JWSException("Invalid JWS"))

    def verify(self, jws, alg = None, **kw):
        if not jws:
            raise (JWSException("Cannot verify empty JWS"))
        try:
            (header_str, payload_str, signature) = jws.split('.')
            header = cjson.decode(base64.b64decode(header_str))
            if alg is None:
                alg = header.get('alg', 'NONE')
            try:
                sigcheck = self._verify.get(alg[:2].upper())
            except KeyError, ex:
                logger.error("Invalid JWS Sign method specified %s", str(ex))
                raise(JWSException("Unsupported encoding method specified"))
            return sigcheck(alg,
                            header,
                            '%s.%s' % (header_str, payload_str),
                            signature)
        except ValueError, ex:
            logger.error("JWS Verification error: %s", ex)
            raise(JWSException("JWS has invalid format"))

    def _sign_NONE(self, alg, header, sbs):
        """ No encryption has no encryption.
            duh.
        """
        return None;

    def _get_sha(self, depth):
        depths = {'256': sha256,
                 '384': sha384,
                 '512': sha512}
        if depth not in depths:
            raise(JWSException('Invalid Depth specified for HS'))
        return depths.get(depth)

    def _sign_HS(self, alg, header, sbs):
        server_secret = self._config.get('jws.server_secret', '')
        signature = hmac.new(server_secret, sbs,
                             self._get_sha(alg[2:])).digest()
        return '%s.%s' % (sbs, base64.urlsafe_b64encode(signature))

    def _sign_RS(self, alg, header, sbs):
        priv_key_u = self._config.get('jws.rsa_key_path', None)
        if priv_key_u is None:
            raise(JWSException("No private key found for RSA signature"))
        bio = BIO.openfile(priv_key_u)
        rsa = RSA.load_key_bio(bio)
        if not rsa.check_key():
            raise(JWSException("Invalid key specified"))
        digest = self._get_sha(alg[2:])(sbs).digest()
        signature = rsa.sign_rsassa_pss(digest)
        return '%s.%s' % (sbs, base64.urlsafe_b64encode(signature))

    def _verify_NONE(self, alg, header, sbs, signature):
        """ There's really no way to verify this. """
        return len(sbs) != 0

    def _verify_HS(self, alg, header, sbs, signature):
        server_secret = self._config.get('jws.server_secret', '')
        tsignature = hmac.new(server_secret,
                              sbs,
                              self._get_sha(alg[2:])).digest()
        return (base64.urlsafe_b64encode(tsignature)) == signature

    def _verify_RS(self, alg, header, sbs, signature, testKey=None):
        #rsa.verify(sbs, pubic_key)
        ## fetch the public key
        if testKey:
            pub = testKey
        else:
            pub = fetch_rsa_pub_key(header)
        rsa = RSA.new_pub_key((pub.get('e'), pub.get('n')))
        digest = self._get_sha(alg[2:])(sbs).digest()
        return rsa.verify_rsassa_pss(digest,
                          base64.urlsafe_b64decode(signature))

    def header(self, header = None, alg = None, **kw):
        """ return the stored header or generate one from scratch. """
        if header:
            self._header = header
        if self._header:
            return self._header
        if not alg:
            alg = self._config.get('jws.default_alg', 'HS256')
        self._header = {
            'alg': alg,
            'typ': self._config.get('jws.default_typ', 'IDAssertion'),
            'jku': kw.get('jku', ''),
            'kid': self._config.get('jws.default_kid', ''),
            'pem': kw.get('pem', ''),
            'x5t': self._config.get('jws.default_x5t', ''),
            'x5u': self._config.get('jws.default_x5u', '')

        }
        return self._header


def create_rsa_jki_entry(pubKey, keyid=None):
    keys = cjson.decode(base64.b64decode(pubKey))
    vinz = {'algorithm': 'RSA',
            'modulus': keys.get('n'),
            'exponent': keys.get('e')}
    if keyid is not None:
        vinz['keyid'] = keyid
    return vinz

##REDO
def fetch_rsa_pub_key(header, **kw):
    ## if 'test' defined, use that value for the returned pub key (blech)
    ## extract the target machine from the header.
    if keytype is None and keyname is None:
        raise JWSException('Must specify either keytype or keyname')
    try:
        if 'pem' in header and header.get('pem', None):
            key = base64.urlsafe_b64decode(header.get('pem')).strip()
            bio = BIO.MemoryBuffer(key)
            pubbit = RSA.load_key_bio(bio).pub()
            pub = {
                'n': int(pubbits[0].encode('hex'), 16),
                'e': int(pubbits[1].encode('hex'), 16)
            }
        elif 'jku' in header and header.get('jku', None):
            key = header['jku']
            if key.lower().startswith('data:'):
                pub = cjson.decode(key[key.index('base64,')+7:])
        return pub
        """
        pub = {
            'n': key.get('modulus', None),
            'e': key.get('exponent', None)
        }
        #"""
        # return pub
    except (AttributeError, KeyError), ex:
        logger.error("Internal RSA error: %s" % str(ex))
        raise(JWSException("Could not extract key"))

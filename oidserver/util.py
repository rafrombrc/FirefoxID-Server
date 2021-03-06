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
import hashlib
import cPickle
from base64 import b64encode
import random
import os
import time
from mako.template import Template

from services.util import randchar


_DEFAULT_MOD = """
DCF93A0B883972EC0E19989AC5A2CE310E1D37717E8D9571BB7623731866E61E
F75A2E27898B057F9891C2E27A639C3F29B60814581CD3B2CA3986D268370557
7D45C2E7E52DC81C7A171876E5CEA74B1448BFDFAF18828EFD2519F14E45E382
6634AF1949E5B535CC829A483B8A76223E5D490A257F05BDFF16F2FB22C583AB
"""
_DEFAULT_MOD = long("".join(_DEFAULT_MOD.split()), 16)
_DEFAULT_GEN = 2
_PROTO_2 = "http://specs.openid.net/auth/2.0"
_PROTO_1 = "http://openid.net/signon/1.1"


def xor(x, y):
    if len(x) != len(y):
        raise ValueError('Inputs to strxor must have the same length')
    xor = lambda (a, b): chr(ord(a) ^ ord(b))
    return "".join(map(xor, zip(x, y)))


def get_nonce():
    now = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    rand_chars = ''.join([randchar() for i in range(6)])
    return now + rand_chars


def btwoc(value):
    res = cPickle.dumps(value, 2)
    return res[3 + ord(res[3]):3:-1]


def unbtwoc(value):
    load = chr(len(value)) + value[::-1] + '.'
    return cPickle.loads('\x80\x02\x8a' + load)


def create_handle(assoc_type):
    """Creates an association handle.

    Args:
        assoc_type: HMAC-SHA1 or HMAC-SHA256

    Returns:
        secret, association handle
    """
    if assoc_type == 'HMAC-SHA1':
        size = 20
    elif assoc_type == 'HMAC-SHA256':
        size = 32
    else:
        raise NotImplementedError(assoc_type)
    secret = os.urandom(size)
    uniq = b64encode(os.urandom(4))
    handle = '{%s}{%x}{%s}' % (assoc_type, int(time.time()), uniq)
    return secret, handle


def get_dh_key(pubkey, session_type, secret, gen=None, mod=None):
    """Returns a Diffie-Hellman encoded key

    Args:
        - the public key of the other side
        - session_type: DH-SHA1 or DH-SHA256
        - secret: the shared secret
        - gen: generator. default to 2
        - mod: modulus, default to the default openid prime

    Return: base64(crypted(pubkey) xor mac_key), btwoc(pub)
    """
    if mod is None:
        mod = _DEFAULT_MOD
    if gen is None:
        gen = _DEFAULT_GEN
    # building the DH signature
    dh_private = random.randrange(1, mod - 1)
    dh_public = pow(gen, dh_private, mod)
    dh_shared = btwoc(pow(pubkey, dh_private, mod))
    if session_type == 'DH-SHA1':
        crypt = lambda x: hashlib.sha1(x).digest()
    else:
        crypt = lambda x: hashlib.sha256(x).digest()
    dh_shared = crypt(dh_shared)
    mac_key = xor(secret, dh_shared)
    return b64encode(mac_key), b64encode(btwoc(dh_public))


""" OpenId Response messages contain the following fields (provided for
    reference):

    OpenID Response Message
      openid.ns
      openid.identity
      openid.mode
      openid.identity
      openid.claimed_id
      openid.return_to
      openid.return_to
      openid.trust_root
      openid.assoc_handle
"""


class IdResMessage(dict):

    def __init__(self, storage, host, expires_in=3600, **params):
        self.storage = storage
        self.expires_in = expires_in
        self.host = host
        self['openid.ns'] = params.get('openid.ns', _PROTO_2)
        self.identity = params.get('openid.identity')
        user = self.identity.split('/')[-1]
        self['openid.mode'] = 'id_res'
        self['openid.identity'] = self.identity
        self['openid.claimed_id'] = params.get('openid.identity')
        return_to = self['openid.return_to'] = params.get('openid.return_to')
        trust_root = params.get('openid.trust_root')
        if trust_root is not None:
            self['openid.trust_root'] = trust_root
        handle = params.get('openid.assoc_handle')
        stateless = handle is None
        if stateless:
            # dumb-mode, no association was created previously
            # creating a private one
            self['openid.assoc_handle'] = self._create_handle()
        else:
            signed = ['mode', 'identity', 'assoc_handle', 'return_to',
                      'sreg.nickname', 'claimed_id']
            if trust_root is not None:
                signed.append('trust_root')
            self.signed = signed
            self['openid.assoc_handle'] = handle
        site = params.get('openid.trust_root')
        if site is None:
            site = return_to
        self.site = site.split('?')[0]    # XXX
        self['openid.sreg.nickname'] = user

    def _create_handle(self):
        client_ns = self['openid.ns']
        if client_ns == _PROTO_1:
            assoc_type = 'HMAC-SHA1'
        else:
            assoc_type = 'HMAC-SHA256'
        secret, handle = create_handle(assoc_type)
        self.storage.add_association(handle, secret, assoc_type, private=True,
                                expires_in=self.expires_in)
        self['openid.response_nonce'] = get_nonce()
        signed = ['return_to', 'response_nonce', 'assoc_handle',
                    'claimed_id', 'identity', 'mode']
        if client_ns == _PROTO_2:
            self['openid.op_endpoint'] = self.host
            signed.append('op_endpoint')
            signed.append('ns')
        if self.get('openid.trust_root') is not None:
            signed.append('trust_root')
        self.signed = signed
        return handle

    def _get_association(self):
        # getting the handle
        handle = self.get('openid.assoc_handle')
        try:
            mac_key, assoc_type, __ = self.storage.get_association(handle)
        except KeyError:
            # handle expired or not existing, switching to dumb mode
            self['openid.invalidate_handle'] = handle
            handle = self['openid.assoc_handle'] = self._create_handle()
            mac_key, assoc_type, __ = self.storage.get_association(handle)

        return mac_key, assoc_type

_TMPL = os.path.join(os.path.dirname(__file__), 'templates')


def get_template(name):
    name = os.path.join(_TMPL, '%s.mako' % name)
    return Template(filename=name)


# The following filters are not guaranteed safe, but should trap most
# unsafe behaviors.
# Exceptionally paranoid string to HTML.
def text_to_html_filter(unsafe_string):
    safe_str = ' abcdefghijklmnopqrstuvwxyz0123456789&#;,.-+@_'
    out = []
    for letter in unsafe_string:
        if letter.lower() in safe_str:
            out.append(letter)
        else:
            out.append('&#%02d;' % ord(letter))
    return ''.join(out)


# only accept urls begining with 'http' (to prevent inline script attacks)
def url_filter(unsafe_url):
    if unsafe_url.lower().startswith('http'):
        return unsafe_url
    return None

import unittest
import urlparse
import base64
import hashlib
import cPickle
import pickle
import random
import itertools
import hmac
import os

from webtest import TestApp
from oidserver.wsgiapp import make_app
from services.config import Config
from oidserver.tests import PRIME, test_config


class TestOpenID(unittest.TestCase):

    def setUp(self):
        config = {'auth.backend': 'dummy',
                  'oidstorage.backend': 'memory',
                  'oid.host': 'http://localhost',
                  'oid.assoc_expires_in': 3600}
        user = test_config.get('auth.credentials').encode('base64')
        self.auth = {'HTTP_AUTHORIZATION': 'Basic ' + user}
        self.app = TestApp(make_app(config))

    def test_bad_requests(self):
        self.app.post('/bla/bla', status=404)
        self.app.post('/', status=400)
        data = {'openid_mode': 'xxx'}
        self.app.post('/', data, status=400)

    def test_yadis(self):
        # testing the yadis page
        headers = {'Accept': 'application/xrds+xml'}
        res = self.app.get('/' + test_config.get('auth.user'),
                           headers=headers)
        self.assertEqual(res.content_type, 'application/xrds+xml')

        # regular html page
        res = self.app.get('/' + test_config.get('auth.user'))
        self.assertEqual(res.content_type, 'text/html')

    def btwoc(self, key):
        res = cPickle.dumps(key, 2)
        return res[3 + ord(res[3]):3:-1]

    def unbtwoc(self, data):
        return cPickle.loads('\x80\x02\x8a' + chr(len(data)) + data[::-1]
                             + '.')

    def _string_xor(self, s1, s2):
        res = []
        for c1, c2 in itertools.izip(s1, s2):
            res.append(chr(ord(c1) ^ ord(c2)))
        return ''.join(res)

    def string_xor(self, x, y):
        if len(x) != len(y):
            raise ValueError('must have the same length')

        xor = lambda (a, b): chr(ord(a) ^ ord(b))
        return "".join(map(xor, zip(x, y)))

    def long2bin(self, value):
        if value == 0:
            return '\x00'
        return ''.join(reversed(pickle.encode_long(value)))

    def test_shared_secret(self):
        # demonstrates how Diffie-Hellman works
        gen = 2
        mod = PRIME

        # client choose a private value
        client_priv = 1234

        # the public value is pow(gen, priv, mod)
        client_pub = pow(gen, client_priv, mod)

        # server choose a private value
        serv_priv = 3456

        # the public value is pow(gen, priv, mod)
        serv_pub = pow(gen, serv_priv, mod)

        # the client does pow(serv_pub, client_priv, mod)
        client_secret = pow(serv_pub, client_priv, mod)

        # the server does the same
        serv_secret = pow(client_pub, serv_priv, mod)

        # they should have now a shared secret
        self.assertEqual(serv_secret, client_secret)

        #
        # Signing
        #

        # let's sign stuff with the shared secret
        data = '123456'
        mac_key = os.urandom(20)
        hash = hmac.new(mac_key, data, hashlib.sha1)
        serv_sig = hash.digest()

        # now let's encrypt the mac_key using the client key
        # enc_mac_key = sha1(client_pub) XOR mac key
        s_key = self.btwoc(pow(client_pub, serv_priv, mod))
        s_key = hashlib.sha1(s_key).digest()
        enc_mac_key = self.string_xor(s_key, mac_key)

        # the client now decrypts the enc_mac_key
        c_key = self.btwoc(pow(serv_pub, client_priv, mod))
        c_key = hashlib.sha1(c_key).digest()
        self.assertEquals(c_key, s_key)

        founded_mac_key = self.string_xor(enc_mac_key, c_key)
        self.assertEqual(mac_key, founded_mac_key)
        hash = hmac.new(founded_mac_key, data, hashlib.sha1)
        client_sig = hash.digest()

        # it should be the same signature
        self.assertEqual(client_sig, serv_sig)

    def _test_associate(self, session_type='DH-SHA1', assoc_type='HMAC-SHA1'):
        if session_type == 'DH-SHA1':
            session_crypt = lambda x: hashlib.sha1(x).digest()
        elif session_type == 'DH-SHA256':
            session_crypt = lambda x: hashlib.sha256(x).digest()
        else:
            session_crypt = lambda x: x

        if assoc_type == 'HMAC-SHA1':
            dh_crypt = hashlib.sha1
        else:
            dh_crypt = hashlib.sha256

        # asking for an association
        data = {
        'openid.ns': "http://specs.openid.net/auth/2.0",
        'openid.mode': "associate",
        'openid.assoc_type': assoc_type,
        'openid.session_type': session_type,
        }

        # build and adding client private + public keys
        client_priv = random.randrange(1, PRIME - 1)
        client_pub = pow(2L, client_priv, PRIME)
        dh_pub = base64.b64encode(self.btwoc(client_pub))
        data['openid.dh_consumer_public'] = dh_pub

        res = self.app.post('/', data, extra_environ=self.auth)

        # let's check if we have the right association info
        data = {}
        for line in res.body.split('\n'):
            line = line.split(':')
            data[line[0].strip()] = line[1].strip()

        if session_type != 'no-encryption':
            enc_mac_key = data['enc_mac_key']
            enc_mac_key = base64.b64decode(enc_mac_key)
        else:
            enc_mac_key = None
            mac_key = data['mac_key']

        # decrypted mac_key
        if enc_mac_key is not None:
            srv_pub = data['dh_server_public']
            srv_pub = self.unbtwoc(base64.b64decode(srv_pub))

            # building the shared secret
            sh_sec = self.btwoc(pow(srv_pub, client_priv, PRIME))
            sh_sec = session_crypt(str(sh_sec))
            if len(sh_sec) != len(enc_mac_key):
                raise ValueError("incorrect DH key size")

            mac_key = self.string_xor(enc_mac_key, sh_sec)

        # let's call checkid_setup now, with the assoc_handle
        # returned by the server
        data = {'openid.ns': 'http://specs.openid.net/auth/2.0',
                'openid.mode': 'checkid_setup',
                'openid.claimed_id': 'tarek',
                'openid.realm': 'realm',
                'openid.identity': 'http://localhost/tarek',
                'openid.assoc_handle': data['assoc_handle'],
                'openid.return_to': 'http://example.com/here'}

        res = self.app.post('/', data, extra_environ=self.auth)

        # clicking on the "continue button"
        res = res.form.submit()

        self.assertEqual(res.status_int, 307)
        parsed = list(urlparse.urlparse(res.location))
        query = urlparse.parse_qs(parsed[4])

        # let's check if we have the right association info
        data = {}
        for key, value in query.items():
            data[key] = value[0]

        # let's test the signature with the previous mac_key
        signed = data['openid.signed']
        sig = data['openid.sig']
        res = []
        for name in signed.split(','):
            value = data['openid.' + name]
            value = '%s:%s\n' % (name, value)
            res.append(value)

        res = ''.join(res)
        transmitted_sig = base64.b64decode(sig)
        computed_sig = hmac.new(mac_key, res, dh_crypt).digest()

        if transmitted_sig != computed_sig:
            raise ValueError('Invalid signature')

    def test_associate_sha1(self):
        self._test_associate('DH-SHA1', 'HMAC-SHA1')

    def test_associate_sha256(self):
        self._test_associate('DH-SHA256', 'HMAC-SHA256')

    def _test_associate_no_encryption(self):
        self._test_associate('no-encryption', 'HMAC-SHA256')

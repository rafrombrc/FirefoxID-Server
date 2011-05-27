""" ***** BEGIN LICENSE BLOCK *****
 * Version: MPL 1.1/GPL 2.0/LGPL 2.1
 *
 * The contents of this file are subject to the Mozilla Public License Version
 * 1.1 (the "License"); you may not use this file except in compliance with
 * the License. You may obtain a copy of the License at
 * http://www.mozilla.org/MPL/
 *
 * Software distributed under the License is distributed on an "AS IS" basis,
 * WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
 * for the specific language governing rights and limitations under the
 * License.
 *
 * The Original Code is __________________________________________.
 *
 * The Initial Developer of the Original Code is
 * J-R Conlin (jrconlin@mozilla.com).
 * Portions created by the Initial Developer are Copyright (C) 2___
 * the Initial Developer. All Rights Reserved.
 *
 * Contributor(s):
 *
 * Alternatively, the contents of this file may be used under the terms of
 * either the GNU General Public License Version 2 or later (the "GPL"), or
 * the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
 * in which case the provisions of the GPL or the LGPL are applicable instead
 * of those above. If you wish to allow use of your version of this file only
 * under the terms of either the GPL or the LGPL, and not to allow others to
 * use your version of this file under the terms of the MPL, indicate your
 * decision by deleting the provisions above and replace them with the notice
 * and other provisions required by the GPL or the LGPL. If you do not delete
 * the provisions above, a recipient may use your version of this file under
 * the terms of any one of the MPL, the GPL or the LGPL.
 *
 * ***** END LICENSE BLOCK ***** """

from oidserver import logger

import base64
import json
import rsa


class JWSException (Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class JWS (Object):
    _header = None      # header information
    _crypto = None      # usually the signature
    _claim = None       # the payload of the JWS
    _config = None      # App specific configuration values

    _encode = {'HS256': self._encode_HS256,
               'RS256': self._enode_RS256,
               'NONE':  self._encode_NONE}
    _decode = {'HS256': self._decode_HS256,
               'RS256': self._decode_HS256,
               'NONE':  self._decode_NONE}

    def __init__(self, config = None, **kw):
        if config:
            self._config = config

        return self

    def encode(self, payload, header = None, **kw):
        if payload is None:
            raise (JWSException("Cannot encode empty payload"))
        header = self.header()
        if header.get('alg', 'NONE') not in self._encode:
            raise (JWSException("Unsupported encoding method specified"))
        crypt = self._encode.get(header['alg'])
        header_str = base64.urlsafe_b64encode(json.dumps(header))
        payload_str = base64.urlsafe_b64encode(json.dumps(payload))
        sbs = "%s.%s" % (header_str, payload_str)
        signature = crypt(header, sbs)
        return "%s.%s" % (sbs, signature)

    def decode(self, jws, **kw):
        if jws is None:
            raise (JWSException("Cannot decode empty JWS"))
        try:
            (header_str, payload_str, signature) = jws.split('.')
            header = json.loads(base64.urlsafe_b64decode(header_str))
            if header.get('alg', 'NONE') not in self._decode:
                raise (JWSException("Unsupported decoding method specified"))
            decrypt = self._decode.get(header['alg'])
            signature = ## TODO Finish
        except ValueError:
            raise (JWSException("JWS has invalid format"))


    def header(self, header, **kw):
        pass

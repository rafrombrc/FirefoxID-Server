/* ***** BEGIN LICENSE BLOCK *****
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
 * The Original Code is Mozilla verified email prototype.
 *
 * The Initial Developer of the Original Code is Mozilla.
 * Portions created by the Initial Developer are Copyright (C) 2011
 * the Initial Developer. All Rights Reserved.
 *
 * Contributor(s):
 *  Michael Hanson <mhanson@mozilla.com>
 *  Rob Miller <rmiller@mozilla.com>
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
 * ***** END LICENSE BLOCK ***** */

/*
 * Add support for verifying / serializing JWT objects using RSAKey objects rather than
 * private keys in PEM format.
 *
 */

(function() {
  function NoSuchAlgorithmException(message) {
    this.message = message;
    this.toString = function() { return "No such algorithm: "+this.message; };
  }

  function RSAKeySHAAlgorithm(hash, rsaKey) {
    if (hash == "sha1") {
      this.hash = "sha1";
    } else if (hash == "sha256") {
      this.hash = "sha256";
    } else {
      throw new NoSuchAlgorithmException("JWT algorithm: " + hash);
    }
    this.rsaKey = rsaKey;
  }

  RSAKeySHAAlgorithm.prototype = {
    update: function _update(data) {
      this.data = data;
    },
    finalize: function _finalize() {
    },
    sign: function _sign() {
      var hSig = this.rsaKey.signString(this.data, this.hash);
      return base64urlencode(base64urldecode(hex2b64(hSig))); // TODO replace this with hex2b64urlencode!
    },
    verify: function _verify(sig) {
      var result = this.rsaKey.verifyString(this.data, b64urltohex(sig));
      return result;
    }
  };

  function constructAlgorithm(jwtAlgStr, rsaKey) {
    if ("RS256" === jwtAlgStr) {
      return new RSAKeySHAAlgorithm("sha256", rsaKey);
    } else if ("RS384" === jwtAlgStr) {
      throw new NotImplementedException("RSA-SHA384 not yet implemented");
    } else if ("RS512" === jwtAlgStr) {
      throw new NotImplementedException("RSA-SHA512 not yet implemented");
    } else {
      throw new NoSuchAlgorithmException("Unknown algorithm: " + jwtAlgStr);
    }
  }

  jwt.WebToken.prototype.rsaKeySerialize = function _rsaKeySerialize(rsaKey) {
      var header = jsonObj(this.pkAlgorithm);
      var jwtAlgStr = header.alg;
      var algorithm = constructAlgorithm(jwtAlgStr, rsaKey);
      var algBytes = base64urlencode(this.pkAlgorithm);
      var jsonBytes = base64urlencode(this.objectStr);

      var stringToSign = algBytes + "." + jsonBytes;
      algorithm.update(stringToSign);
      var digestValue = algorithm.finalize();

      var signatureValue = algorithm.sign();
      return algBytes + "." + jsonBytes + "." + signatureValue;
  };

  jwt.WebToken.prototype.rsaKeyVerify = function _rsaKeyVerify(rsaKey) {
      var header = jsonObj(this.pkAlgorithm);
      var jwtAlgStr = header.alg;
      var algorithm = constructAlgorithm(jwtAlgStr, rsaKey);
      algorithm.update(this.headerSegment + "." + this.payloadSegment);
      algorithm.finalize();
      return algorithm.verify(this.cryptoSegment);
  };
})();
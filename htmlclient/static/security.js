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

var security = {};

(function() {
  // public vars
  security.ID_KEY_PREFIX = 'vep.id';
  security.CERTS = security.ID_KEY_PREFIX + '.certs';
  security.RSA_BITS = 1024;
  security.RSA_EXP = "10001";

  // private vars
  var rsa = new RSAKey();

  function generateKeyPair() {
    rsa.generate(security.RSA_BITS, security.RSA_EXP);
    var modulus = jwt.base64urlencode(rsa.n.toByteArray());
    var pubExponent = jwt.base64urlencode(rsa.e);
    var privExponent = jwt.base64urlencode(rsa.d.toByteArray());
    var pub = {
      "algorithm": "RSA",
      "modulus": modulus,
      "exponent": pubExponent
    };
    var priv = {
      "algorithm": "RSA",
      "modulus": modulus,
      "exponent": privExponent
    };
    return {
      "publicKey": {"keyvalues": [pub]},
      "privateKey": {"keyvalues": [priv]}
    };
  }

  security.generateKeyPair = generateKeyPair;
})();
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
 *  Richard Newman <rnewman@mozilla.com>
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
 * Client-side Javascript module that implements the UA portion of the Mozilla
 * Identity API.
 *
 * see:
 *   https://wiki.mozilla.org/Identity
 *   https://wiki.mozilla.org/Identity/Verified_Email_Protocol/Latest)
 *
 */

(function() {
  function log(m) {
    if (console.log)
      console.log("navigator.id: " + m);
  }

  // Don't do anything if the browser provides its own navigator.id
  // implementation. If we already injected one here -- typically the case if
  // you reload the page -- then unhook it and start from scratch.
  // This avoids errors like "attempt to run compile-and-go script on a cleared
  // scope".
  if (navigator.id) {
    if (navigator.id.isInjected) {
      // Remove the existing object and its handlers.
      log("Unhooking existing navigator.id.");
      navigator.id.unhook();
    } else {
      log("Not swizzling.");
      return;
    }
  }

  // TODO: err msg if no local storage support
  var localStorage = window['localStorage'];

  function _setStorage(key, value) {
    var fullKey = security.ID_KEY_PREFIX + '.' + key;
    localStorage[fullKey] = value;
  }

  function _getStorage(key) {
    var fullKey = security.ID_KEY_PREFIX + '.' + key;
    var value = localStorage[fullKey];
    // normalize local storage misses to a null return
    if (typeof(value) === "undefined") {
      value = null;
    };
    return value;
  }

  function _getCertsObject() {
    // retrieve and deserialize id certificates object, or return empty object
    // if it doesn't exist
    var certs = _getStorage(security.CERTS_KEY);
    if (certs === null) {
      certs = {};
    } else {
      certs = JSON.parse(certs);
    };
    return certs;
  }

  function _setCertsObject(certs) {
    // serialize and store the id certs object
    _setStorage(security.CERTS_KEY, JSON.stringify(certs));
  }

  function _getCertRecord(email) {
    // fetches id cert record from local storage, may return null

    // top level `certs` object contains all id cert records for the current
    // origin, keyed by email address
    var certs = _getCertsObject();
    var certRecord = certs[email];
    if (typeof(certRecord) === "undefined") {
      return null;
    };

    // TODO: clarify cert format
    if (typeof(certRecord.publicKey) === "undefined" ||
        typeof(certRecord.privateKey) === "undefined") {
      // invalid key pair, throw it away
      return null;
    };
    return certRecord;
  }

  function _setCertRecord(email, certRecord) {
    // stores an id cert record to local storage, keyed by email address;
    // overwrites any pre-existing cert records stored for the same address
    var certs = _getCertsObject();
    certs[email] = certRecord;
    _setCertsObject(certs);
  }

  log("Swizzling navigator.id.");
  navigator.id = {
    isInjected: true,    // Differentiate from a built-in object.
    unhook: null,        // This gets built later, once we know what to unhook!

    registerVerifiedEmail: function registerVerifiedEmail(email, callback) {
      var certRecord = _getCertRecord(email);
      if (certRecord !== null) {
        var cert = certRecord.cert;
        if (cert.exp /// XXX STOPPED HERE
      };
      if (certRecord === null) {
        // TODO: "please wait" UI
        var keyPair = _generateKeyPair();
        certRecord = {'email': email,
                      'issuer': document.domain,
                      'publicKey': keyPair.publicKey,
                      'privateKey': keyPair.privateKey
                     }
        _setCertRecord(email, certRecord);
      };
      callback(email, keyPair.pub);
    },

    registerVerifiedEmailCertificate: function registerCert(certJwt, updateUrl) {
      // expects identity certificate JWT (Javascript Web Token).  parses the
      // JWT, fetches the cert record for the id cert's email address, and
      // stores the cert in the cert record.  throws an error if no cert record
      // exists for the address, or if the public key in the cert doesn't match
      // the public key in the stored key pair
      var webToken = jwt.WebTokenParser.parse(certJwt);
      var objectStr = jwt.base64urldecode(webToken.payloadSegment);
      var cert = JSON.parse(objectStr);
      // TODO: compare the 'issuer' in the cert w/ the origin for this request?
      // email address is stored as 'id' field in the id cert
      var email = cert.id;
      var certPubKey = cert.publicKey;
      var certRecord = _getCertRecord(email);
      if (certRecord === null) {
        throw "No ID certificate record exists for " + email;
      };
      if (JSON.stringify(certRecord.publicKey) != JSON.stringify(cert.publicKey)) {
        throw "Public key mismatch";
      };
      certRecord.cert = cert;
      _setCertRecord(email, certRecord);
    },

    getVerifiedEmail: function getVerifiedEmail(callback) {
    }
  }
})();
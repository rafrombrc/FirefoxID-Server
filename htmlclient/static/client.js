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
  // TODO: err msg if no local storage support
  var localStorage = window['localStorage'];
  var VEP_KEY_PREFIX = 'moz.vep';
  var CERTS_KEY = 'certs';
  var AUD_KEY = 'audiences';

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

  function _getStoredObject(key) {
    /* Fetch JSON from local storage stored under the specified key (plus our
    VEP prefix), deserialize, and return the resulting object.  Return empty
    object if specified key doesn't exist. */
    var obj = _getStorage(key);
    if (obj === null) {
      obj = {};
    } else {
      obj = JSON.parse(obj);
    };
    return obj;
  }

  function _storeObject(key, obj) {
    /* Serialize and store the specified object in local storage. */
    _setStorage(key, JSON.stringify(obj));
  }

  function _getCertRecord(email) {
    /* fetches id cert record from local storage, may return null */

    // top level `certs` object contains all id cert records for the current
    // origin, keyed by email address
    var certs = _getStoredObject(CERTS_KEY);
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
    /* stores an id cert record to local storage, keyed by email address;
    overwrites any pre-existing cert records stored for the same address */
    var certs = _getStoredObject(CERTS_KEY);
    certs[email] = certRecord;
    _storeObject(CERTS_KEY, certs);
  }

  function _getIdForAudience(audience) {
    var audiences = _getStoredObject(AUD_KEY);
    var audRecord = audiences[audience];
    if (typeof(audRecord) === "undefined") {
      // no previous id provided for this audience, user must specify
      // XXX: TODO
    };
  }

  function _getCertRecordForAudience(audience) {
    /* return a valid id certificate for the id (i.e. email address) associated
    w/ the specified audience, if possible */
    audienceEmail = _getIdForAudience(audience);
  }

  clientApi = {
    registerVerifiedEmail: function registerVerifiedEmail(email) {
      var certRecord = _getCertRecord(email);
      if (certRecord !== null) {
        var cert = certRecord.cert;
        var now = new Date();
        if (cert.exp < now.getTime()/1000) {
          certRecord = null;
        } else if (certRecord.iss != document.location.hostname) {
          // XXX: is this actually correct?
          certRecord = null;
        } else {
          // cert is valid, return nulls which will be passed to the callback as per spec
          return {'email': null, 'publicKey': null};
        };
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
      return {'email': email, 'publicKey': keyPair.pub};
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
      var certPubKey = cert['moz-vep-publicKey'];
      var certRecord = _getCertRecord(email);
      if (certRecord === null) {
        throw "No ID certificate record exists for " + email;
      };
      if (JSON.stringify(certRecord.publicKey) != JSON.stringify(certPubKey)) {
        throw "Public key mismatch";
      };
      certRecord.cert = cert;
      certRecord.certUpdateUrl = updateUrl;
      _setCertRecord(email, certRecord);
    },

    getVerifiedEmail: function getVerifiedEmail() {
      var audience = document.location.hostname;
      var certRecord = _getCertRecordForAudience(audience);
      if (certRecord === null) {
        // TODO
      };
      var assertion = _generateAssertion(certRecord);
      navigator.id.onVerifiedEmail(assertion);
    }
  };

  /* postMessage handling and reponding */

  function log(m) {
    if (console.log)
      console.log("VEPClient: " + m);
  }

  function send(dest, message, origin) {
    if (!origin)
      throw "Refusing to send to open origin.";
    log("Sending message to origin " + JSON.stringify(origin));
    dest.postMessage(JSON.stringify(message), origin);
  }

  function receive(event, message) {
    if (!message.operation || !message.args) {
      throw('Malformed VEP Client postMessage request');
    };
    if (!clientApi[message.operation]) {
      throw('Undefined VEP Client API call: ' + message.operation);
    };
    result = clientApi[message.operation](message.args);
    if (message.responseNeeded) {
      // send the result as a postMessage back to the original window
      send(event.source, result, origin(event));
    }
  }

  function handlePostMessage(event) {
    if (!origin(event)) {
      log("Rejecting message with null origin.");
      return;
    };
    var message;
    try {
      message = JSON.parse(event.data);
    } catch (ex) {
      // Drop it on the floor.
      log("Malformed JSON message: ignoring.");
      return;
    };
    // Hooray! Valid origin and JSON body.
    try {
      receive(event, message);
    } catch (ex) {
      // Error was raised, notify postMessage caller
    };
  }

})();
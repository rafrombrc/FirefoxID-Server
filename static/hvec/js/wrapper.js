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
 * Client-side Javascript module that provides the User Agent portion of the
 * Mozilla VEP API.
 *
 *   https://wiki.mozilla.org/Identity/Verified_Email_Protocol/Latest
 *
 * Note that this module doesn't actually the actual work required by the
 * VEP, but instead delegates to an invisible iframe which has loaded code
 * from the identity provider that does.  This is b/c the implementation
 * depends on id certificates and other information being stored in local
 * storage, and all access to that localstorage must happen from the same
 * origin.
 *
 */

(function() {
  function log(m) {
    if (console.log)
      console.log("VEPClient: " + m);
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

  var identityOrigin   = "https://localhost";   //CHANGE HOST
  var iframe           = document.createElement("iframe");
  iframe.style.display = "none";
  iframe.src           = identityOrigin + "/hvec/vec_iframe.html";

  var popup;
  var popupRequestMessage;

  var postHandlers = {
    'popup': function popup(args) {
      var popupFeatures = "scrollbars=yes" +
        ",left="   + (args.left   || 80)  +
        ",top="    + (args.top    || 80)  +
        ",height=" + (args.height || 475) +
        ",width="  + (args.width  || 475);
      log("In popup handler: " + JSON.stringify(args));
      popup = window.open(args.uri, args.target, popupFeatures);
      if (!popup) {
        throw "Verified email fetcher found no popup!";
      }
      popupRequestMessage = args;
      log("Created popup: " + popup);
    },

    'closePopup': function closePopup(args) {
      log("In closePopup handler: " + JSON.stringify(args));
      if (popup) {
        popup.close();
      }
      popup = null;
      popupRequestMessage = null;
    }
  };

  var vepChan = Channel.build(iframe.contentWindow, identityOrigin, 'vepScope');
  vepChan.bind('popup', postHandlers.popup);
  vepChan.bind('closePopup', postHandlers.popup);

  log("Swizzling navigator.id.");
  navigator.id = {
    isInjected: true,    // Differentiate from a built-in object.
    unhook: null,        // This gets built later, once we know what to unhook!

    registerVerifiedEmail: function registerVerifiedEmail(email, callback) {
      function finishRegisterVerifiedEmail(result) {
        callback(result.publicKey);
      }
      vepChan.call({'method': 'registerVerifiedEmail',
                    'params': email,
                    'success': finishRegisterVerifiedEmail});
    },

    registerVerifiedEmailCertificate: function registerCert(certJwt, updateUrl, errorUrl) {
      vepChan.notify({'method': 'registerVerifiedEmailCertificate',
                      'params': [certJwt, updateUrl, errorUrl]});
    },

    getVerifiedEmail: function getVerifiedEmail() {
      vepChan.notify({'method': 'getVerifiedEmail'});
    },

    unhook: function unhook() {
        // Try our best to do each of these things.
        try {
          window.removeEventListener("message", handlePostMessage, true);
        } catch (ex) {}
        try {
          document.body.removeChild(iframe);
        } catch (ex) {}
        delete navigator.id;
      }
    }
  };

  document.body.appendChild(iframe);

})();

var MOZ_ID_KEY_PREFIX = 'moz.id';
var RSA_BITS = 1024;
var RSA_EXP = 10001;
var security = {};

(function() {
  var rsa = new RSAKey();
  // TODO: err msg if no local storage support
  var localStorage = window['localStorage'];

  function _setStorage(key, value) {
    var fullKey = MOZ_ID_KEY_PREFIX + '.' + key;
    localStorage[fullKey] = value;
  }

  function _getStorage(key) {
    var fullKey = MOZ_ID_KEY_PREFIX + '.' + key;
    var value = localStorage[fullKey];
    // normalize local storage misses to a null return
    if (typeof(value) === "undefined") {
      value = null;
    }
    return value;
  }

  function _setKeyPairsObject(keyPairs) {
    // serialize and store the keyPairs object
    _setStorage('keyPairs', JSON.stringify(keyPairs));
  }

  function _getKeyPairsObject() {
    // retrieve and deserialize keyPairs object, or return empty object if it
    // doesn't exist
    var keyPairs = _getStorage('keyPairs');
    if (keyPairs === null) {
      keyPairs = {};
    } else {
      keyPairs = JSON.parse(keyPairs);
    }
    return keyPairs;
  }

  function _setKeyPair(email, keyPair) {
    // stores a key pair to local storage, keyed by email address; overwrites
    // any pre-existing keyPairs stored for the same address
    var keyPairs = _getKeyPairsObject();
    keyPairs[email] = keyPair;
    _setKeyPairsObject(keyPairs);
  }

  function _getKeyPair(email) {
    // fetches key pair from local storage, may return null

    // top level `keyPairs` object contains all key pairs registered for the
    // current origin, keyed by email address
    var keyPairs = _getKeyPairsObject();
    var keyPair = keyPairs[email];
    if (typeof(keyPair) === "undefined") {
      return null;
    }

    if (typeof(keyPair.pub) === "undefined" ||
        typeof(keyPair.priv) === "undefined") {
      // invalid key pair, throw it away
      return null;
    }
    return keyPair;
  }

  function _generateKeyPair(bits, exp) {
    rsa.generate(parseInt(bits), exp.toString());
    var pub = {
      "algorithm": "RS256",
      "keyData": rsa.n.toString(16)
    };
    var priv = {
      "algorithm": "RS256",
      "keyData": rsa.d.toString(16)
    };
    return {
      "pub": pub,
      "priv": priv
    };
  }

  function getUAKeyPair(email) {
    // returns the user agent keypair for a given email address for the current
    // origin
    var keyPair = _getKeyPair(email);
    if (keyPair === null) {
      // TODO: "please wait" UI
      keyPair = _generateKeyPair(RSA_BITS, RSA_EXP);
      _setKeyPair(email, keyPair);
    }
    return keyPair;
  }

  security.getUAKeyPair = getUAKeyPair;
})();
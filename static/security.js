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
    return localStorage[fullKey];
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

  function _setKeyPair(issuer, email, keyPair) {
    // stores a key pair from local storage, keyed by issuer and then email
    // address; overwrites any pre-existing keyPairs stored for the same keys

    // fetch top level `keyPairs` object
    var keyPairs = _getKeyPairsObject();

    // get key pair container for the issuer, creating if necessary
    issuerKeyPairs = keyPairs[issuer];
    if (typeof(issuerKeyPairs) === "undefined") {
      issuerKeyPairs = {};
      keyPairs[issuer] = issuerKeyPairs;
    }

    // store the key pair by email address, write out the keyPairs object
    issuerKeyPairs[email] = keyPair;
    _setKeyPairsObject(keyPairs);
  }

  function _getKeyPair(issuer, email) {
    // fetches key pair from local storage, may return null

    // fetch top level `keyPairs` object, then look up keypair sets by issuer
    var keyPairs = _getKeyPairsObject();
    issuerKeyPairs = keyPairs[issuer];
    if (typeof(issuerKeyPairs) === "undefined") {
      return null;
    }

    // finally fetch the actual key pair filed by email address
    keyPair = issuerKeyPairs[email];
    if (typeof(keyPair) === "undefined") {
      return null;
    }

    var priv = keyPair.priv;
    if (typeof(keyPair.pub) === "undefined" ||
        typeof(keyPair.priv) === "undefined") {
      // incomplete key pair, throw it away
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

  function getUAKeyPair(issuer, email) {
    // returns the user agent keypair, creating if necessary
    var keyPair = _getKeyPair(issuer, email);
    if (keyPair === null) {
      // TODO: "please wait" UI
      keyPair = _generateKeyPair(RSA_BITS, RSA_EXP);
      _setKeyPair(issuer, email, keyPair);
    }
    return keyPair;
  }

  security.getUAKeyPair = getUAKeyPair;
})();
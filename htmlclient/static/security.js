var security = {};

(function() {
  // public vars
  security.MOZ_ID_KEY_PREFIX = 'moz.id';
  security.KEYPAIRS_KEY = 'keyPairs';
  security.RSA_BITS = 1024;
  security.RSA_EXP = 10001;

  // private vars
  var rsa = new RSAKey();
  // TODO: err msg if no local storage support
  var localStorage = window['localStorage'];

  function _setStorage(key, value) {
    var fullKey = security.MOZ_ID_KEY_PREFIX + '.' + key;
    localStorage[fullKey] = value;
  }

  function _getStorage(key) {
    var fullKey = security.MOZ_ID_KEY_PREFIX + '.' + key;
    var value = localStorage[fullKey];
    // normalize local storage misses to a null return
    if (typeof(value) === "undefined") {
      value = null;
    };
    return value;
  }

  function _setKeyPairsObject(keyPairs) {
    // serialize and store the keyPairs object
    _setStorage(security.KEYPAIRS_KEY, JSON.stringify(keyPairs));
  }

  function _getKeyPairsObject() {
    // retrieve and deserialize keyPairs object, or return empty object if it
    // doesn't exist
    var keyPairs = _getStorage(security.KEYPAIRS_KEY);
    if (keyPairs === null) {
      keyPairs = {};
    } else {
      keyPairs = JSON.parse(keyPairs);
    };
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
    };

    if (typeof(keyPair.pub) === "undefined" ||
        typeof(keyPair.priv) === "undefined") {
      // invalid key pair, throw it away
      return null;
    };
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

  function getKeyPairForEmail(email) {
    // returns the user agent keypair for a given email address for the current
    // origin
    var keyPair = _getKeyPair(email);
    if (keyPair === null) {
      // TODO: "please wait" UI
      keyPair = _generateKeyPair(security.RSA_BITS, security.RSA_EXP);
      _setKeyPair(email, keyPair);
    };
    return keyPair;
  }

  function getAllKeyPairs() {
    return _getKeyPairsObject();
  }

  function storeIdCert(idCertJwt) {
    // expects identity certificate JWT (Javascript Web Token), stores the
    // associated ID cert with the key pair for the email address embedded
    // within the cert; throws an error if no key pair exists for the address,
    // or if the public key in the cert doesn't match the public key in the
    // stored key pair
    var webToken = jwt.WebTokenParser.parse(idCertJwt);
    var objectStr = jwt.base64urldecode(webToken.payloadSegment);
    var idCertBody = JSON.parse(objectStr);
    // TODO: compare the 'issuer' in the cert w/ the origin for this request?
    // email address is stored as 'id' field in the id cert
    var email = idCertBody.id;
    var pubKey = idCertBody.publicKey;
    var keyPair = _getKeyPair(email);
    if (keyPair === null) {
      throw "No key pair exists for " + email;
    };
    if (keyPair.pub.algorithm !== idCertBody.publicKey.algorithm ||
        keyPair.pub.keyData !== idCertBody.publicKey.keyData) {
      throw "Public key mismatch";
    };
    keyPair.idCert = JSON.stringify(idCertBody);
    _setKeyPair(email, keyPair);
  }

  security.getKeyPairForEmail = getKeyPairForEmail;
  security.getAllKeyPairs = getAllKeyPairs;
  security.storeIdCert = storeIdCert;
})();
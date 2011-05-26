describe("Security Public API", function () {
  var originalKeyPairsKey;
  var originalRSABits;
  var localStorage = window['localStorage'];
  var TEST_KEYPAIRS_KEY = 'testKeyPairs';
  var STORAGE_NAME = security.MOZ_ID_KEY_PREFIX + '.' + TEST_KEYPAIRS_KEY;

  var testEmail = 'sasquatch@example.com';
  var testIssuer = 'sasquatch.example.com';
  var now = new Date();
  var oneYearFromNow = new Date(now.getTime());
  oneYearFromNow.setFullYear(oneYearFromNow.getFullYear()+1);

  beforeEach(function() {
    originalKeyPairsKey = security.KEYPAIRS_KEY;
    originalRSABits = security.RSA_BITS;
    security.KEYPAIRS_KEY = TEST_KEYPAIRS_KEY;
    security.RSA_BITS = 256;
  });

  afterEach(function () {
    localStorage.removeItem(STORAGE_NAME);
    security.KEYPAIRS_KEY = originalKeyPairsKey;
    security.RSA_BITS = originalRSABits;
  });

  function _generateIdCertBody(pubKey) {
    return {"id": testEmail, "valid-until": JSON.stringify(oneYearFromNow),
            "issuer": testIssuer, "publicKey": pubKey}
  }

  function _generateJwt(pubKey, obj) {
    var objStr = JSON.stringify(obj);
    var webToken = new jwt.WebToken(objStr, {'alg': 'RS256'});
    return webToken.serialize(pubKey);
  }

  it("should start with an empty keyPairs object", function() {
    expect(security.getAllKeyPairs()).toEqual({});
  });

  it("should generate a key pair for an email address", function() {
    var keyPair = security.getKeyPairForEmail(testEmail);
    expect('pub' in keyPair).toBeTruthy();
    expect('priv' in keyPair).toBeTruthy();
    expect('idCert' in keyPair).toBeFalsy();
  });

  it("should return the same key pair later", function() {
    var keyPair = security.getKeyPairForEmail(testEmail);
    expect(keyPair).toEqual(security.getKeyPairForEmail(testEmail));
  });

  it("should store id cert from jwt w/ right key pair", function() {
    var keyPair = security.getKeyPairForEmail(testEmail);
    var pubKey = keyPair.pub;
    var idCertBody = _generateIdCertBody(pubKey);
    var idCertJwt = _generateJwt(pubKey, idCertBody);
    expect('idCert' in keyPair).toBeFalsy();
    security.storeIdCert(idCertJwt);
    expect('idCert' in keyPair).toBeTruthy();
    keyPair = security.getKeyPairForEmail(testEmail);
    expect('idCert' in keyPair).toBeTruthy();
    expect(keyPair.idCert).toEqual(idCertBody);
  });
});
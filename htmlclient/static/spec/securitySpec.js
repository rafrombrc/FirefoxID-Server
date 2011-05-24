describe("Security Public API", function () {
  var originalKeyPairsKey;
  var originalRSABits;
  var localStorage = window['localStorage'];
  var TEST_KEYPAIRS_KEY = 'testKeyPairs';
  var STORAGE_NAME = security.MOZ_ID_KEY_PREFIX + '.' + TEST_KEYPAIRS_KEY;

  var test_email = 'sasquatch@example.com';

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

  it("should start with an empty keyPairs object", function() {
    expect(security.getAllKeyPairs()).toEqual({});
  });

  it("should generate a key pair for an email address", function() {
    var keyPair = security.getKeyPairForEmail(test_email);
    expect('pub' in keyPair).toBeTruthy();
    expect('priv' in keyPair).toBeTruthy();
    expect('idCert' in keyPair).toBeFalsy();
  });

  it("should return the same key pair later", function() {
    var keyPair = security.getKeyPairForEmail(test_email);
    expect(keyPair).toEqual(security.getKeyPairForEmail(test_email));
  });
});
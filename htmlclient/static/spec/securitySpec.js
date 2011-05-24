describe("Security Public API", function () {
  var originalKeyPairsKey;
  var localStorage = window['localStorage'];
  var TEST_KEYPAIRS_KEY = 'testKeyPairs';
  var storageKey = MOZ_ID_KEY_PREFIX + '.' + 'keyPairs'

  beforeEach(function() {
    originalKeyPairsKey = security.KEYPAIRS_KEY;
    security.KEYPAIRS_KEY = TEST_KEYPAIRS_KEY;
  });

  afterEach(function () {
    security.KEYPAIRS_KEY = originalKeyPairsKey;
  });

  it("should start with an empty keyPairs object", function() {
    expect(security.getAllKeyPairs()).toEqual({});
  });
});
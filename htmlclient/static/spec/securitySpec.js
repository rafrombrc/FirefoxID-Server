describe("Security Public API", function () {
  var originalKeyPairsKey;
  var localStorage = window['localStorage'];
  var TEST_KEYPAIRS_KEY = 'testKeyPairs';
  var STORAGE_NAME = security.MOZ_ID_KEY_PREFIX + '.' + TEST_KEYPAIRS_KEY;

  var test_email = 'sasquatch@example.com';

  beforeEach(function() {
    originalKeyPairsKey = security.KEYPAIRS_KEY;
    security.KEYPAIRS_KEY = TEST_KEYPAIRS_KEY;
  });

  afterEach(function () {
    localStorage.removeItem(STORAGE_NAME);
    security.KEYPAIRS_KEY = originalKeyPairsKey;
  });

  it("should start with an empty keyPairs object", function() {
    expect(security.getAllKeyPairs()).toEqual({});
  });
});
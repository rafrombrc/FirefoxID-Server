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
    var rsKeyPEM = window.atob("LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlFb3dJQkFBS0NBUUVBeEV5bWpsbVBNVXN2RTVQVStBVFNOd2c0dkxtS2tEMzFTRzI4WkRuN0RoNmMxT0FoCllYL3lFcCs1QlhxOHliQmtScGZDLzdzclJRNCtUeG5uR3NwUHQvZVF5S2ZORjgwbHd5NFRSQS9TYlJDallmK04KVHE2ZTh2M1FIOE05U2NpS01HME9MbXZNbk9nVi9tVFJVd1pTdUxPZXRaTEQxNmdDZ2QxR0cwc01BS0JYYkpaZwoyb3oxdEp1bFBPdGFDWW1ReHU1M2NWSGtmRHZGLzRLMG1LMTIyam8xRnh4UGtBbjNOcU1Db2QzR3hpOFVIaE5iCjBzOHhsVzl6Ynlvc2RmdGJqOWI1VGRCTXBSUzlmRWllc1psQVpxOGtPa1lUUnJVVHJZdjI1d2pYaEhCSGNOeUsKVEhDbjVYZGl2dTdzZFBMZVBEajhuSFJuTGo0cmtTaktwaUZHYXdJREFRQUJBb0lCQVFDZDVib2p6czVyckRwVgoyUmY1MklidlZXR3VET0QwWGFJcmZIbUpkVW9JZFg5WmpGL05lWWxTaWIvZU5IZ2ZGQS9VNk1ZbHhueHJzNlZUCkkxYk9LZVl0NktsQmZoaHZDTWxUVW9DVXd0VlVmWW11amswditTNUo3dmUyVk9tN3E5L2NUQnlZSW9ZWHdHZlEKbFcvN0JKOE5pdzRpcDhkNGRPQnZiWG16QW83SkFNZERBTXdDZlNPTFBwRVprMXdsc1Q5YjBHaHZnMHZsVU5oTwpISGRmSjYzRlRyY2xZUFZETXNuNmU1aEZOSXRCenVQeDlvUjN2eENmQjQyZkY5TVpYRnpIamx0NUd1Q0hqOUN0CkJ4UlJxdENsb1JLR3V1ak9DUkEzM1NaS3p3Snd2KzkzZkxZVkh0anBYOGsvczhjYkpFcFVzdDlxdGxZTmoxSFoKMmc2Q0t0QkJBb0dCQVBEQ0o4R20wYjQ2Y0FiLzY3MXMxeFJJYnRDbjZxSEtwVHFwN1RJT2FxajlOQWJqeDFrYgozTUJ1MUc4OVZzMFRvOWlZejB2M1VZcUMyZ0kzTnd2SEtZZTBReENaVE84Y2kvaVRxa3ZsbXZNbG1XK2ZwQnlRCmhzay8vTXMzQlcvM0VNRVhiUklLNXA3akFMa2ZyemVqY0pIeG5scTkzdlJob2lSZUsrMWVqTEVqQW9HQkFOQzUKK01HNU5wZnJjaUR0akhQelp5YlRUd0t2b0wzVEpvMWNESHJaaE5nWWNUOTgrSkM1bzcwWTIvSXprcHZPUmFuagpiUEIrcEhFM2ZYZ0dHVHFESGNtbyt2RnQ4MkZvRGVMdmRRb0NJblduMzJtTUlvQUthdE8zM3oreUFmcjg2eUZOCjIzdlNQL0JndXBrVEYvZ0ltY3QvK2tlWU12WDB6KzhsUVR6eUpMNFpBb0dBVldhWmthQ3AvODljMDY3T0lXaE4KTnIybXlVNzI5S01jVHgzZHJJYmVvTWtJUG5WbnpoMExCaHVLTVZkUnhmYjBoSzFYd3Z1Y3FnUldicmpGUnVGRAp3d1pYVDdrQlNFUVpCbmppekg5S29uc3czUjZFcVRrL0JuNHpIcWFLd0Rla2NzbnJmNTNzUm1vQlpLbHZqczNqCjdYRUdtZXVGL2F2d1J2UThvcnVLTG44Q2dZQTM0b01yQXpjTngvbGZ2WnFNZFJBYVFodDJnYVdORFpyVjRGNXIKQ2hCYWQzamk0Y2YvbitTcVBaeXVKWWJNZHBjS1hKMFBheWtHTXpCQjBZZ3h0V2RsVmZ3U1pqanl6SlJqUFcvZAp4U0tLMCs2cWFOM1g0SElueTZSWGZvYXZOOGFRdlRMVjNUNUhVdTdEQzJ5d2VVVU1TbkN0ZUorMFlON0hqZmNBCnBXaVhDUUtCZ0N5SDVETTFWb1NNaCtVSXJ6WW5vVVVKY1ZDL3EyWGp0Zkdod3JhVUJhTTZ6OVNXaFg2amZMSGkKNW9qc2ZjSE5vU3h5a0hJQllXNmovQ1ZVSmpoY2NRa0pnR2tHRmoxZkh2cTVpWGZPaTFjMWl6djQxQ0REWGRQKwpKcTNNbHMzaDVXTnJ5RTdhTTQ5S3JaRWpjbytzajVRc3dMMnkwTk1weHdHRE9palpqS0lyCi0tLS0tRU5EIFJTQSBQUklWQVRFIEtFWS0tLS0tCg==");
    var objStr = JSON.stringify(obj);
    var algStr = JSON.stringify({'alg': 'RS256'});
    var webToken = new jwt.WebToken(objStr, algStr);
    return webToken.serialize(rsKeyPEM);
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
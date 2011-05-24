function populateKeyPairsList() {
  var keyPairsList = $('#keypairs-list');
  var keyPairs = security.getAllKeyPairs();
  for (var email in keyPairs) {
    if (keyPairs.hasOwnProperty(email)) {
      var keyPair = keyPairs[email];
      var li = $('<li><em>' + email + '</em>: '
                 + JSON.stringify(keyPair) + '</li>\n');
      keyPairsList.append(li);
    }
  }
}

function doInit() {
  populateKeyPairsList();
}
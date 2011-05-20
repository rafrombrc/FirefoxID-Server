function populateKeyPairsList() {
  var keyPairsList = $('#keypairs-list');
  var keyPairs = security.getAllKeyPairs();
  for (var address in keyPairs) {
    if (keyPairs.hasOwnProperty(address)) {
      keyPair = keyPairs[address];
      var li = $('<li><em>' + address + '</em>: '
                 + JSON.stringify(keyPair) + '</li>\n');
      keyPairsList.append(li);
    }
  }
}

function doInit() {
  populateKeyPairsList();
}
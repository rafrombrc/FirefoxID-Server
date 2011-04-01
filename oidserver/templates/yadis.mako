<?xml version="1.0" encoding="UTF-8"?>
<xrds:XRDS xmlns:xrds="xri://$xrds" xmlns="xri://$xrd*($v*2.0)"
                       xmlns:openid="http://openid.net/xmlns/1.0">
  <XRD>
    <Service priority="20">
      <Type>http://specs.openid.net/auth/2.0/signon</Type>
      <URI>${host}</URI>
      <LocalID>${host}/${user}</LocalID>
    </Service>

    <Service priority="10">
      <Type>http://openid.net/signon/1.1</Type>
      <URI>${host}</URI>
      <LocalID>${host}/${user}</LocalID>
    </Service>

  </XRD>
</xrds:XRDS>


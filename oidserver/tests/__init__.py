from services.auth.dummy import DummyAuth

PRIME = """
DCF93A0B883972EC0E19989AC5A2CE310E1D37717E8D9571BB7623731866E61E
F75A2E27898B057F9891C2E27A639C3F29B60814581CD3B2CA3986D268370557
7D45C2E7E52DC81C7A171876E5CEA74B1448BFDFAF18828EFD2519F14E45E382
6634AF1949E5B535CC829A483B8A76223E5D490A257F05BDFF16F2FB22C583AB
"""
PRIME = long("".join(PRIME.split()), 16)

## default values:
test_config = {'auth.user': 'good@example.com',
               'auth.pass': 'good',
               'userinfo.uid': 'test_api_1',
               'auth.credentials': 'jrandomperson:password',
               'oidstorage.backend': 'redis',
               'uidcookiestorage.backend': 'memory',
               'config.target': 'localhost'}

# config values of interest
#       auth.valid_until        TTL for cert (300 seconds)
#       auth.issuer             Auth Identifier (untrusted)
#       auth.server_secret      Crypto Secret ('')
#       db.host                 Database Host (127.0.0.1)
#       oidstorage.backend      (memory | mongo | redis)
#                               currently redis is not yet finalized

class FakeRequest(object):
    """
     Fake request object for testing only
    """

    def __init__(self,
                 path="/",
                 environ=None,
                 post=None,
                 get=None,
                 host="localhost:80", # match UnitTest's fake localhost
                 **kw):
        self.path_info = path
        self.environ = environ or {}
        self.POST = post or {}
        self.params = get or {}
        self.params.update({'audience': 'test.example.org'})
        self.host = host

class FakeAuthTool(DummyAuth):
    """
     Fake Auth tool returns invalid for any password containing "bad"
     The username is hashed by this point.
    """

    def authenticate_user(self, *userpass):
        if "bad" in userpass[1]:
            return None
        return 'test_api_1'

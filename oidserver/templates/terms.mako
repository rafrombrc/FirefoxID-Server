<html>
 <head>
<%
 from oidserver import VERSION
 import urlparse
 import urllib


 # pre-define variables so that mako doesn't puke and die.
 error = pageargs.get('error', '')
 output = pageargs.get('output', 'html')
 config = pageargs.get('config', {})
 email = pageargs.get('email', '')
 request = pageargs.get('request', {'params': {}})
 default_url = config.get('auth.default_url')
 login_host = config.get('oid.login_host', 'https://localhost')
 audience = request.params.get('audience','')

%>
## The following meta is checked by the make test.
%if len(error) > 0:
 <meta name="error" content="${error}" />
%endif
 <link rel="stylesheet" type="text/css" href="/s/style.css" />
 <meta name="page" content="terms" />
 </head>
 <body>
  <header><h1>FirefoxID Terms</h1></header>
  <main>
  <h2>Terms of Use</h2>
  <p>{Terms of use go here}<p>
  </main>
  <footer>
    <form action='${login_host}/${VERSION}/login' method='POST'>
     <div class="footer">
     <div class="buttons">
     <button class="go_back" disabled>Go Back</button>
     <button type="cancel" class="cancel">Cancel</button>
     <button type="submit" name="terms" value="Y" class="submit">I Agree</button>
     <div>
     <input type="hidden" name="audience" value="${audience}" />
     <input type="hidden" name="email" value="${email}" />
    </form>
    </footer>
    <script src="/s/user.js"></script>
 </body>
</html>

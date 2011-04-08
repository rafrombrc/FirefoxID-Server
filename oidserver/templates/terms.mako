<html>
 <head>
<%
 import urlparse
 import urllib


 # pre-define variables so that mako doesn't puke and die.
 error = pageargs.get('error', '')
 output = pageargs.get('output', 'html')
 config = pageargs.get('config',{})
 default_url = config.get('auth.default_url')
 add_email_url = pageargs.get('auth.add_email_url',
  config.get('auth.add_email_url',default_url))
 manage_acct_url = pageargs.get('auth.manage_acct_url',
  config.get('manage_acct_url',default_url))
 audience = '<span class="error">Invalid Site</span>'
 if len(request.params.get('audience', '')) > 0:
  audience = urlparse.urlsplit(request.params.get('audience')).netloc
 use_default_checked = pageargs.get('use_default_checked', False)
 user = pageargs.get('response', {}).get('user', None)
 emails = []
 default = ''
 if user is not None:
  emails = user.get('emails', [''])
  default = user.get('pemail', emails[0])

 # Append the user's default email. That's the key we use to get to the user's
 # account management page.
 manage_acct_url = "%s%s" % (manage_acct_url, urllib.quote(default))

 # Sanitize the output value (since it comes from untrusted sources)
 if output.lower() not in ('html', 'json'):
  output = 'html'
 icnt = 0

%>
## The following meta is checked by the make test.
%if len(error) > 0:
 <meta name="error" content="${error}" />
%endif
 <link rel="stylesheet" type="text/css" href="/s/style.css" />
 <meta name="page" content="terms" />
 </head>
 <body>
  <h1>Please Read</h1>
  <div class="text">
  <h2>Terms of Use</h2>
  <p>{Terms of use go here}<p>
  </div>
    <form action='/1/login' method='POST'>
     <div class="footer">
     <div class="buttons">
     <button class="go_back" disabled>Go Back</button>
     <button type="cancel" class="cancel">Cancel</button>
     <button type="submit" name="terms" value="Y" class="submit">I Agree</button>
     <div>
     <input type="hidden" name="audience" value="${audience}" />
    </form>
    <script src="user.js"></script>
 </body>
</html>

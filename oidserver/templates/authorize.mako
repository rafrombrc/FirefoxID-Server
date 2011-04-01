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
 <meta name="page" content="associate" />
 </head>
 <body>
  <h1>Sign in with Your Mozilla ID</h1>
    %if len(error) > 0:
     <div class="error">${error}</div>
    %endif
    <p>How would you like to identify yourself to <b>${audience}</b></p>
    <form action='/1/authorize' method='POST'>
    % for email in emails:
     <p><input class="radio" id="email_${icnt}" type="radio" name="temail" value="${email}"
     % if email == default:
      checked
     % endif
     />
     <label for="email_${icnt}">${email}</label></p>
     <% icnt = icnt + 1 %>
    % endfor
     <div class="footer">
     <div class="commands">
     <a href="${add_email_url}">Add a new email address</a>
     <a href="${manage_acct_url}">Manage my Mozilla ID</a>
     </div>
     <div class="buttons">
     <button class="go_back" disabled>Go Back</button>
     <button type="cancel" class="cancel" onclick="window.close()">Cancel</button>
     <button type="submit" class="submit">Sign In</button>
     <div>
     <input type="hidden" name="audience" value="${audience}" />
    </form>
 </body>
</html>

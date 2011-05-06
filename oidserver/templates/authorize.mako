<!DOCTYPE HTML>
<html>
 <head>
<%
 from oidserver import VERSION
 import urlparse
 import urllib


 # pre-define variables so that mako doesn't puke and die.
 error = pageargs.get('error', '')
 output = pageargs.get('output', 'html')
 config = pageargs.get('config',{})
 request = pageargs.get('request',{'params': {}})

 audience = request.params.get('audience','')
 user = pageargs.get('response', {}).get('user', {})
 emails = []
 default = ''
 if user:
  emails = user.get('emails', [''])
  default = user.get('pemail', '')
 default_url = config.get('oid.login_host', 'https://localhost')

 use_default_checked = pageargs.get('use_default_checked', False)
 # Append the user's default email. That's the key we use to get to the user's
 # account management page.
 manage_acct_url = "%s/%s" % (default_url, urllib.quote(default))

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
 <header>
  <h1>Sign in with Your Firefox ID</h1>
 </header>
 <main>
    %if len(error) > 0:
     <div class="error">${error}</div>
    %endif
    %if emails:
    <p>How would you like to identify yourself to <b>${audience}</b></p>
    <form action='${default_url}/${VERSION}/authorize' id="formauth" method='POST'>
    % for email in emails:
     <p><input class="radio" id="email_${icnt}" type="radio" name="temail" value="${email}"
     % if email == default:
      checked
     % endif
     />
     <label for="email_${icnt}">${email}</label></p>
     <% icnt = icnt + 1 %>
    % endfor
    </form>
    %else:
<%
  pemail = user.get('pemail','')
%>
    <p>You have not yet verified an email. Please select an email to verify:</p>
    <form action='${default_url}/${VERSION}/manage_email' id="formauth" method="POST">
     %if pemail:
     <p><input class="radio" id="vemail_pe" type="radio" name="unv" value="${pemail}"><label for="vemail">${pemail}</label></p>
     %endif
     <p><input class="radio" id="vemail_o" type="radio" name="unv" placeholder="Other email">
     <input type="text" name="unv" placeholder="Other email"></p>
     <input type="hidden" name="act" value="add">
     <input type="hidden" name="audience" value="${audience}" />
    </form>
    %endif
 </main>
 <footer>
     <div class="register">
     <a href="${manage_acct_url}">Manage my Firefox ID</a>
     </div>
     <div class="buttons">
     <button class="go_back" disabled>Go Back</button>
     <button type="cancel" class="cancel" onclick="window.close()">Cancel</button>
     <button type="submit" class="rsubmit" value="formauth">Sign In</button>
     <div>
 </footer>
 <script src="/s/user.js"></script>
 </body>
</html>

<html>
 <head>
<%
  import urlparse

  # pre-define variables so that mako doesn't puke and die.
  error = pageargs.get('error', '')
  output = pageargs.get('output', 'html')
  config = pageargs.get('config',{})
  default_url = config.get('auth.default_url')
  forgot_url = pageargs.get('auth.forgot_url', default_url)
  id_help_url = pageargs.get('auth.id_help_url', default_url)
  id_create_url = pageargs.get('auth.id_create_url', default_url)
  id_learn_url = pageargs.get('auth.id_learn_url', 'default_url')
  request = pageargs.get('request', {'params': {}})
  audience = request.params.get('audience', '');
  audience_name = urlparse.urlsplit(audience).netloc
  use_default_checked = pageargs.get('use_default_checked', False)

  # Sanitize the output value (since it comes from untrusted sources)
  if output.lower() not in ('html', 'json'):
   output = 'html'

%>
## The following meta is checked by the make test.
%if len(error) > 0:
 <meta name="error" content="${error}" />
%endif
 <link rel="stylesheet" type="text/css" href="/s/style.css" />
 </head>
 <body>
  <h1>Sign in with Your Firefox ID</h1>
    %if len(error) > 0:
     <div class="error">${error}</div>
    %endif
    <p>Use your Firefox ID to sign in to
    %if len (audience) == 0:
    <div class="error">Invalid Site</div>
    %else:
    <b>${audience_name}</b>
    %endif
    </p>
    <form action='login' method='POST'>
    <p><label for="email">Email</label>
     <input type="text" name="email"></input></p>
    <p><label for="password">Password</label>
     <input type="password" name="password"></input>
     <a href="${forgot_url}">I forgot my password</a></p>
     <input type="hidden" name="output" value="${output}" />
     <input type="hidden" name="audience" value="${audience}" />
    <p class="useDefault"><input type="checkbox" name="use_default"
     ${use_default_checked} /><label for="use_default">Use my default
     identity</label> <a href="${id_help_url}">Identity?</a>
     <div class="footer">
     <div class="register"><b>Don't have a Firefox ID?</b>
     <a href="${id_create_url}">Create one</a> now or
     <a href="${id_learn_url}">learn why</a>
     <div class="buttons">
     <button class="cancel" type="cancel">Cancel</input>
     <button class="submit" type="submit">Sign in</input>
     </div>
     </div>
    </form>
 </body>
</html>

<%
    email = pageargs.get('email','')
    user = pageargs.get('user',{})
    config = pageargs.get('config',{})
    admin_url = (config.get('oid.login_host','https://localhost')  +
                    '/' +
                    user.get('pemail','login'))

%><!DOCTYPE HTML>
<html>
<head>
<link rel="stylesheet" type="text/css" href="/s/style.css" />
<meta name="page" content="conf_email" />
<head>
<body>
<header>
<h1>Email Confirmed</h1>
</header>
<main>
<p>Thanks! We've confirmed the email address</p>
<div class="email">${email|h}</div>
<p>and added it to your account. You may now use that address when logging
into new sites.</p>
</main>
<footer>
<p><a href="${admin_url}">Go to the admin console</a></p>
</footer>
</body>
</html>
<%

    config = pageargs.get('config',{})
    user = pageargs.get('user',{})
    request = pageargs.get('request',{})
    email = pageargs.get('email','')
    admin_url = (config.get('oid.login_host','https://localhost')  +
                    '/' +
                    user.get('pemail','1/login'))

%><!DOCTYPE HTML>
<html>
<head>
<link rel="stylesheet" type="text/css" href="/s/style.css" />
<meta name="page" content="confirm" />
<title>Confirmation email generated</title>
</head>
<body>
<header></header>
<h1>Confirmation email sent</h1>
<div class="message">
<p> Thanks! We've sent a confirmation email to</p>
<div class="email">${email|h}</div>
<p>You should receive that message soon. If not, please check your trash or spam
folders in case it may have been caught by a filter. You may request another
confirmation mail by visiting your <a href="${admin_url}">admin console</a>
</p>
</div>
<footer>
<p><a href="${admin_url}">Return to the admin console</a></p>
</footer>
</body>
</html>
<%
    """ This document is the email validation template.
        Be sure to include the from_addr, to_addr (and the blank lines
        between the header and body of the email), as well as the verify_url

        The email is sent out as plain text. HTML formatted email will require
        a bit of reworking of the auth.send_validate_email() function.
    """

%>From: ${from_addr}
To: ${to_addr}
% if pageargs.get('reply_to',None):
Reply-To: ${reply_to}
% endif
Subject: Please confirm your FirefoxID email address


In order to use the email address you provided, we have to make sure you
control it. Please click on the following link to confirm you control this
email address:

${verify_url}

You may need to copy and paste the url into the address bar of your
chosen browser if your email client doesn't detect links.

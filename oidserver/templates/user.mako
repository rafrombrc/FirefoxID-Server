<%

  host = pageargs.get('host', 'localhost')
  login_host = pageargs.get('login_host', 'localhost')
  user = pageargs.get('user', 'unknown')
  user_info = pageargs.get('user_info',{})
  sites = pageargs.get('sites', [])

  unv_emails = user_info.get('unv_emails', {})
  site = {}
%><html>
 <head>
  <link rel="stylesheet" type="text/css" href="/s/style.css" />
   <link rel="openid.server" href="${host}"/>
   <link rel="openid2.provider" href="${host}"/>
   <link rel="openid2.local_id" href="${host}/${user}"/>
 </head>
 <body>
<%doc>

        This file will not
        be used, ideally. It is provided for legacy OpenID2
        reasons, as well as a placeholder for a future dashboard.

</%doc>
<header></header>
    <h1>Welcome to <span class="username">${user|h}</span>'s page.</h1>
    <div id="error"></div>
    %if user_info:
     %if sites:
    <h2>Authorized sites:</h2>
    <table class="user" id="sites">
    <tr><th>Site</th><th>ID</th><th></th></tr>
      %for site in sites:
      <tr><td>${site['site_id']}</td><td>${site['email']|h}</td>
      <td class="button"><button class="disable" value="site_id=${site['site_id']|u}" disabled >Disable</button></td></tr>
      %endfor
    </table>
     %endif
    <div id="user">
    <h2>Your information</h2>
    <p>Please note: The following information should be considered public and
    may be shared with the sites you connect to. It is optional and provided
    here for convienence.</p>
    <form action="https:/1/manage_info" method="POST">
    <p><input name="sname" value="${user_info.get('sname','')|u}" placeholder="First Name" /></p>
    <p><input name="fname" value="${user_info.get('fname','')|u}" placeholder="Last Name" /></p>
    <p><button class="submit" type="submit">Update Info</button></p>
    </form>
    </div>
    <div id="emails">
    <h2>Additional Emails</h2>
    % if user_info.get('emails',False):
    <ul>
    % for email in user_info.get('emails'):
    % if email != user_info.get('pemail'):
    <li>${email}</li>
    % endif
    % endfor
    </ul>
    %endif
    <form action="https:/1/manage_email" method="POST">
    <p><input name="unv" value="" placeholder="Additional Email"/>
    <button class="submit" type="submit" name="act" value="add">Add Email</button></p>
    </form>
     %if unv_emails:
     <h3>Unverified Emails:</h3>
    <table class="user" id="unv_emails">
    <tr><th>Email</th><th.button></th></tr>
      %for email in unv_emails.keys():
      <tr><td>${email|entity}
      <td class="button"><button class="unv validate" value="act=add&unv=${email|u}">Resend</button></td>
      <td class="button"><button class="unv remove" value="act=del&unv=${email|u}">Forget</button></td>
      </tr>
      %endfor
     </table>
     %endif
    <script type="text/javascript" src="/s/user.js" ></script>
    %else:
## User is not logged in
<p>Enjoy this random picture of a kitten:<br>
<%doc>

    The kitten is not needed, but useful to me at the moment. Eventually,
    lonesome kitty will go away.

</%doc>
<img alt="lonesome kitty is lonesome" src="data:image/jpg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAkGBwgHBgkIBwgKCgkLDRYPDQwMDRsUFRAWIB0iIiAdHx8kKDQsJCYxJx8fLT0tMTU3Ojo6Iys/RD84QzQ5Ojf/2wBDAQoKCg0MDRoPDxo3JR8lNzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzf/wAARCABOAE4DASIAAhEBAxEB/8QAGwAAAQUBAQAAAAAAAAAAAAAABAACAwUGAQf/xAAyEAABAwMCBAUCBAcAAAAAAAABAgMRAAQhBRIiMUFRBhNhgZEycUJDofAUI1KxwdHh/8QAFwEBAQEBAAAAAAAAAAAAAAAAAgMBAP/EAB8RAAMBAAICAwEAAAAAAAAAAAABEQIhMRJRAxNBkf/aAAwDAQACEQMRAD8AzCl1Na25uHNpKgeYAG4n27U1LLbZl9RKx+W3n5PT2pXF1wQ440ywfwJO1Pv396mkBJsPDzNsna00hTiSYXgx79/t80OsuPZdWTmYnFDNvtgcLiCD1SqRTnrxphJLigAOs0zVmEobAwINdAjkkeuKq162wlW1KFqMxyou11G2uY4tp6BWDXRiCwrM5+a7uX3MUitMCBzGJ61zfIgZrjoIqk/8phHWVexpxMCQDSBJnJrToCoMfgGetTWjxZcLiREDnHKhW4IxM09ODyI9qFOpYn+Gu3Qm6s0PrP5iRsWB6kf5rP69astsPrtipSAOFKiJB+/WrZl4hIHnhqCUBalcwelNc05aiGUSqTG7biela++BrrkzTaRchpYGPLQrHx/cUrdKXb1i2IMpa3FQ5yeVbvwj4IXcsPObj5Ib3thXNKlDiT8j9apGtDdsbx5bqVKeWobzGAYnaPQAgU2mlQJpuEsWjYSU2aViAPMelwj2OB8VOlDPCthlDJUnj2ICQrsY+akXYONp3LUPJUdxHeMxQwc85xTgHATw/aMUMxoeuyTpk8qZ/MPE3PYkYpCTAHKKapwpwZA7TSCCoRHMVKFYgkj7Gmfeo1uQJFSQSv1EC5WG3XNrQVxCcx3q80i2OoptrHTnXk3La5ELUUuD1zj271SPqcD6SlKQg9QOfetZ4VfTZvN3IbQXEHIHWr5XNDpzMPR/B1lfWOnO22qOIXcJlBcJgrTnaSO8Y9p61idds9TstRF9qdytmxU4VJYaSr6eif6emT60Tq+sXV7qbb7S32kqAStKHoCwJIx3qw8Q6sdcsW7cslATE5n9iqP0Y4kn7PNr1d6LxLibt5xhUhKHFDhT0OImuWph1TaCkDnG6Ioq+tW2HHEJTuKzmcZqGzaWlKi4hCYjaE8oqPjCloQlKxxBCscyM1CpeT9VdU0ecR6xTZWMJcd9iTRMjE4RtwDQVwspTz5Ua4Z6ewFBvokGKyCK7Tb4POOtrgKnAOJitVpTnklJBJTGc96xq7fZdodQkhU5jrWrZsdRZYbeFspSFJ3ABBVHxVU3+E3OmbaxtWX0hyAYPTvRGopbs7YqbAKiORHzWa0/Xl6ZbbryydYTICVBBIPz1oy9Gsa0sGytdrChIWVwSPQVS/0l4898FHfIC1nO5QO0EiYmhHXOIIAmMT3o/V9I1HS7RD14EhSlbcHl+81WMI2gKVk9TUdVcMumiTeoABMkq5CakZd2JJSopk5VtBJ/0KYhO444U9YOT6U1UcoEChYa+ROAe57dKgWmUkdaJWpSk7SfWhwcx+tZTQXyQVhUAwQfvXoGm+LbNLDfnILakjiRskTIGI6AT+lYkjpieldSIHqKefkeegaytdmh8W62zq9s5ZWzag2VhQdOO+IpaV4nu7O3Sw+2h1CVJEpO3hHT1xNUjQMSTg00kFW2K77NWneGYWuq6zc6x5bdwUoSiOAEwoicn5qtVAhEjnkjrSbwQEkiadG4YwBRenpnJI6mSn6uXSolJzy+acZCR3PI0lZORH2rBn//2Q==" />
</p>
<p><a href="${login_host}/1/login">Login</a></p>
    %endif
<footer></footer>
 </body>
</html>

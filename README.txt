Firefox ID server

NOTE: THIS IS AN EARLY ALPHA VERSION DESIGNED TO SHOWCASE THE PROTOCOL. SOME 
BACKEND FUNCTIONS ARE EMULATED FOR STAND ALONE SERVERS.

:Introduction:

The FirefoxID server is the back end component which allows a demonstration
of the FirefoxID process. For a detailed description of that process, design
and protocol, please refer to: https://wiki.mozilla.org/MozillaID

To assist in understanding, the current configuration runs without ssl, hoe

We welcome discussion. 


:Notes for setup:

This module is constructed to use Python and VirtualEnv. 

::Basic Requirements::
The following packages are required. For simplicity, I have limited these to
the corresponding debian package names, however it should be reasonably 
simple to determine the corresponding package names for your system:

    python-2.6
    python-virtualenv

We run the package via nginx, although there's no requirement for deployment.
    nginx

some additional optional packages
    python-2.6-dev
    python-2.6-profiler
    redis-server  (v.2.0.4 +)
    python-redis
    python-ldap
    python-openid
    gnuplot (for bench reports)
    python-gnuplot
    libsasl2-dev
    libldap-dev
    libssl-dev
    nginx
    mongodb

via the virtualenv easyinstall: 
    gunicorn

:Installation:
    #. pull the latest repository 
    #. modify openid.conf
    #. $ make build
    #. $ mkdir -p /etc/oidserver; cp etc/*.{ini,conf} /etc/oidserver
    #. $ bin/gunicorn -w 1 oidserver.run
        (Note: multiple workers are useful, but not recommended for debugging.
        if you are interested in living in the debugger, you may also wish to
        include -t 300 which will time out worker threads after 300 seconds,
        rather than the default 30 seconds.)

This should bring up a server.

If you are using nginx as your server platform:
    #. $ cp conf/nginx/conf.d/*.conf /etc/nginx/conf.d
    Please note that due to nginx conf processing considerations, astatic.conf needs
    to be processed before other "s*" based rules are resolved.


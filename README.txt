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

The "out of the box" setup for the server creates an in-memory, stand-alone server suitable for running on a single machine and testing the protocol. Some additional steps are required, please refer to the Stand-alone section for additional details.

This module is constructed using Python 2.6 and Virtualenv 1.4.5+

::Basic Requirements::
The following packages are required. For simplicity, I have limited these to
the corresponding debian package names, however it should be reasonably 
simple to determine the corresponding package names for your system:

    python-2.6
    python-virtualenv
    (the following are required for stand-alone)
        openldap-devel
        openssl-devel 
    or
        libsasl2-dev
        libssl-dev 
    libcurl3-dev

We run the package via nginx, although there's no requirement for deployment.
    nginx

some additional optional packages
    python-2.6-dev
    python-2.6-profiler         (required for profile testing)
    gnuplot                     (for profile bench reports)
    python-gnuplot
    redis-server [v.2.0.4 +]    (alt. storage)
    python-redis                (or easy_install redis)
    mongodb
    pymongo     
    python-ldap                 (if using LDAP)
    libsasl2-dev
    libldap-dev
    libssl-dev
    mysql-devel                 (required for some installs using LDAP)

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

If you are using nginx as your server platform:
    #. $ cp conf/nginx/conf.d/*.conf /etc/nginx/conf.d
    Please note that due to nginx conf processing considerations, astatic.conf
    needs to be processed before other "s*" based rules are resolved.
    #. FOR UBUNTU Configurations:
        The packaged nginx configuration files are a bit different under 
        Ubuntu (10.04). You will need to either modify the 
        /etc/nginx/nginx.conf file or the individual nginx configuration
        files, or use the included conf/nginx/nginx.conf.UBUNTU file.


This should bring up a server.

:: Running a "stand-alone, in-memory server" ::
A stand-alone, in-memory server is a useful tool to play with the protocol 
without requiring the overhead of mongo, LDAP or other tools. The major 
issue with such a server is that restarting the server will flush all entries.

You will need to install nginx in order to use the stand-alone, in-memory 
server. 

::: Steps :::
#. Pull the latest repository

#. mkdir -p /etc/oidserver; cp etc/*.* /etc/oidserver

#. cp conf/nginx/conf.d/* /etc/nginx/conf.d/

#. customize for your platform.
It is STRONGLY recommended that you run nginx on port 80 and that your
/etc/nginx/nginx.conf contains the following server declaration in 
the http section:

    server {
        listen 80 default;
        include /etc/nginx/conf.d/*.conf;
    }

In addition, you should add the following declaration to 
/etc/nginx/conf.d/astatic.conf:

location ^~ /sample/ {
    allow all;
    root /var/www/;
}

#. mkdir -p /var/www/sample/; cp sample/* /var/www/sample

#. /etc/init.d/nginx restart

:: Running the Server ::

To run the server, simply execute:
$ bin/gunicorn -w 5 oidserver.run

For stand-alone servers, you may wish to run:
$ bin/gunicorn -w 1 oidserver.run -t 300

The demonstration page may be viewed at http://localhost/sample/. You should now be able to test the protocol. Email addresses may be anything. Only accounts with a password containing "bad" will be rejected. 


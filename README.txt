Notes for setup:

basic requirements:
	python-2.6
	python-2.6-dev
	python-2.6-profiler
	python-virtualenv

    nginx
    bin/easy-install gunicorn
	
optional:
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

easyinstall: 
    gunicorn

Installation:
	#. untar into a directory
	#. modify openid.conf
	#. $ make build
    #. $ mkdir -p /etc/oidserver; cp etc/*.ini /etc/oidserver
    #. $ bin/gunicorn -w 5 oidserver.run

    #. to benchmark: $ make bench

This should bring up a server.


PRIVATE::
    build.py -- ensure that all installs are up to date.
    paster -- the outermost Russian Doll.
    
    model appears to be like Restlet in that there's a whole lotta wrapper before you get to the candy.

    functional entry point is deps/server-core/services/baseapp.py::__call__
        then calls into entry points as defined in wsgiap.py


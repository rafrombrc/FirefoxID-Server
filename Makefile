APPNAME = server-identity
DEPS = server-core
VIRTUALENV = virtualenv
NOSE = bin/nosetests -s --with-xunit
TESTS = oidserver/tests
PYTHON = bin/python
EZ = bin/easy_install
COVEROPTS = --cover-html --cover-html-dir=html --with-coverage --cover-package=oidserver
COVERAGE = bin/coverage
PYLINT = bin/pylint
PKGS = oidserver
BENCH = bin/fl-run-bench
REPORT = bin/fl-build-report
INSTALL = sudo apt-get install

.PHONY: all build test hudson lint

all:	build

build:
	$(VIRTUALENV) --no-site-packages --distribute .
	touch README.txt
	$(PYTHON) build.py $(APPNAME) $(DEPS)
	$(EZ) nose
	$(EZ) WebTest
	$(EZ) Funkload 
	$(EZ) pylint
	$(EZ) coverage
	$(EZ) pymongo
	$(EZ) rsa
	$(EZ) Beaker
	$(EZ) Mako
	$(EZ) M2Crypto
	$(EZ) python_ldap
	$(EZ) python-cjson
	$(EZ) gunicorn

clean:
	find . -name "*.pyc" -delete
	rm -rf html
	rm -rf loadtests/stress/html
	rm -f  loadtests/stress/stress-bench.xml*

package:
#todo: convert this to an rpm packager.
	$(clean)
	tar -zcvf ../oidserver.tar.gz README.txt Makefile nosetests.xml *.py conf etc loadtests oidserver static pylintrc

test:
	$(NOSE) $(TESTS)

hudson:
	rm -f coverage.xml
	- $(COVERAGE) run --source=oidserver $(NOSE) $(TESTS); $(COVERAGE) xml

lint:
	rm -f pylint.txt
	- $(PYLINT) -f parseable --rcfile=pylintrc $(PKGS) > pylint.txt

bench:
	rm -f loadtests/stress-bench.xml*
	rm -f stress-test.*
	rm -f funkload.*
	cd loadtests; ../$(BENCH) stress.py StressTest.test_simple

bench_report:
	$(REPORT) --html -o html loadtests/stress-bench.xml

# Pre requirements for stand alone server
# (Optional)
sa_preflight:
	$(INSTALL) python-2.6
	$(INSTALL) python-virtualenv
	$(INSTALL) libsasl2-dev
	$(INSTALL) libssl-dev
	$(INSTALL) python-cxx-dev
	$(INSTALL) libldap2-dev
	$(INSTALL) openssl-devel
	$(INSTALL) nginx
	$(INSTALL) swig

# Configure UBUNTU style nginx to point to our config files.
sa_fixnginx:
	cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup-`date +r'%Y%m%d'`
	cp conf/nginx/nginx.conf.UBUNTU /etc/nginx/nginx.conf
	cp conf/nginx/conf.d/* /etc/nginx/conf.d/*
#	Some versions of nginx won't allow ssl and non ssl to live in the same dir
	ln -s /etc/nginx/conf.d /etc/nginx/conf.d/ssl

# Run an instance of the Stand Alone server.
runsa:
	bin/gunicorn -w1 oidserver.run -t 300 --log-file - --log-level info

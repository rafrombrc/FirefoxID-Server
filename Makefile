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

.PHONY: all build test hudson lint

all:	build

build:
	$(VIRTUALENV) --no-site-packages --distribute .
	touch README.txt
	$(PYTHON) build.py $(APPNAME) $(DEPS)
	$(EZ) nose
	$(EZ) WebTest
	$(EZ) Funkload==1.14        #Currently locked due to a dependency issue in Funkload.
	$(EZ) pylint
	$(EZ) coverage
	$(EZ) pymongo
	$(EZ) Beaker
	$(EZ) Mako
	$(EZ) python_ldap
	$(EZ) gunicorn

clean:
	find . -name "*.pyc" -delete
	rm -rf html
	rm -rf loadtests/stress/html
	rm -f  loadtests/stress/stress-bench.xml*

package:
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

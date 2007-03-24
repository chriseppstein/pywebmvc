# $Id: //depot/ui/web/main/pywebmvc/Makefile#11 $

PYTHON?=python2.4
SU_PYTHON?=sudo python2.4

BUILD_DIR=build/lib
TEST_BUILD_DIR=testbuild/lib
API_DIR=doc/api
PYTHON_BUILD_PATH=$(BUILD_DIR)
PYTHON_TEST_PATH=$(TEST_BUILD_DIR)

.PHONY: dist clean install build test api

all: build

clean:
	$(PYTHON) setup.py clean
	rm -rf MANIFEST dist build testbuild REVISION setup.cfg $(API_DIR) bin

REVISION:
	p4 changes -m 1 '#have' | sed -n 's/^Change \([0-9]*\) .*/\1/p' > REVISION

setup.cfg: setup.cfg.in REVISION VERSION
	export REVISION=`cat REVISION` && export VERSION=`cat VERSION` && cat setup.cfg.in | sed -e "s/RELEASE/$$REVISION/" | sed -e "s/VERSION/$$VERSION/" > setup.cfg

# rpmbuild runs python instead of python2.4, so create a local bin dir with a
# python that links to python2.4, and prepend it to PATH
bin/python:
	mkdir -p bin
	ln -s `which python2.4` $@

dist:: clean setup.cfg bin/python
dist::
	$(PYTHON) setup.py sdist
	set -x; PATH=$$PWD/bin:$$PATH $(PYTHON) setup.py bdist_rpm
	export REVISION=`cat REVISION` && export VERSION=`cat VERSION` && mv dist/pywebmvc-$$VERSION.tar.gz dist/pywebmvc-$$VERSION-$$REVISION.tar.gz

install: build
	$(SU_PYTHON) setup.py install

build:
	$(PYTHON) setup.py build

testbuild: build
	rm -rf testbuild
	cp -r build testbuild
	cp -r test/stub/* testbuild/lib

test: testbuild
	(export PYTHONPATH=$(PYTHON_TEST_PATH); $(PYTHON) testbuild/lib/pywebmvc/unittest/__init__.py)

api: testbuild
	mkdir -p $(API_DIR)
	(export PYTHONPATH=$(PYTHON_TEST_PATH); epydoc -n PyWebMVC -o $(API_DIR) $(TEST_BUILD_DIR)/pywebmvc)
	

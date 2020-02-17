#SHELL := /bin/bash #to be able to execute `source`

.PHONY: build
build: clean
	python setup.py  sdist bdist_wheel

.PHONY: clean
clean:
	rm -rf dist */*.egg-info *.egg-info  build
	rm -rf .test

.ONESHELL:
.PHONY: test
test: build
	bash test/install
	# twine check dist/*	
	# virtualenv .test
	# source .test/bin/activate
	# pip install git+https://github.com/labstreaminglayer/liblsl-Python.git
	# pip install dist/*.whl
	# pytest

.PHONY: upload
upload: build
	twine check dist/*
	twine upload dist/* --verbose
.ONESHELL:
SHELL := /bin/bash
SRC = $(wildcard nbs/*.ipynb)

all: lib docs

.SILENT: docker
docker:
	docker build . -t fl

lib:
	nbdev_build_lib

sync:
	nbdev_update_lib

serve:
	cd docs && bundle-2.7 exec jekyll serve

.PHONY: docs
docs:
	papermill index.ipynb index.ipynb --cwd . --kernel fl
	nbdev_build_docs

run:
	find source -name "*.ipynb" | grep -v .ipynb_checkpoints | xargs -I {} papermill {} {} --cwd source --kernel fl

test:
	nbdev_test_nbs

release: pypi conda_release
	nbdev_bump_version

conda_release:
	fastrelease_conda_package

pypi: dist
	twine upload --repository pypi dist/*

dist: clean
	python -m build --sdist --wheel

install: clean lib clean
	python -m pip uninstall -y flayout
	python -m pip install --upgrade -e .

user_install: clean lib clean
	python -m pip uninstall -y flayout
	python -m pip install --user --upgrade .

fast_user_install: lib
	python -m pip uninstall -y flayout
	python -m pip install --user --upgrade --no-deps .

clean:
	nbdev_clean_nbs
	find . -name "*.ipynb" | xargs nbstripout
	find . -name "dist" | xargs rm -rf
	find . -name "build" | xargs rm -rf
	find . -name "builds" | xargs rm -rf
	find . -name "__pycache__" | xargs rm -rf
	find . -name "*.so" | xargs rm -rf
	find . -name "*.egg-info" | xargs rm -rf
	find . -name ".ipynb_checkpoints" | xargs rm -rf
	find . -name ".pytest_cache" | xargs rm -rf

reset:
	rm -rf flayout
	rm -rf docs
	git checkout -- docs
	nbdev_build_lib
	make clean

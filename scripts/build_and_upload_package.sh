#!/usr/bin/env bash
scripts/clean_package.sh
python setup.py bdist_wheel
twine upload dist/*
scripts/clean_package.sh

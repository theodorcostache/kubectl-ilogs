#!/bin/bash

coverage run -m pytest ilogs_test.py -vv
coverage html --include ilogs.py
coverage report -m --include ilogs.py
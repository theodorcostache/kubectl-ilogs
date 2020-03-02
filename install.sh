#!/bin/bash

echo "Installing dependencies..."
python3 -m pip install --quiet -r requirements.txt
echo "Running tests..."
python3 -m pytest ilogs_test.py || exit 1
echo "Compiling..."
cython ilogs.py --embed || exit 1
gcc -Os -I $(find /usr/include -name python3.*m -print -quit) -o\
        kubectl-ilogs ilogs.c -l $(find /usr/include -name python3.*m -printf "%f" -quit)\
        -lpthread -lm -lutil -ldl || exit 1
echo "Installing..."
mv ./kubectl-ilogs /usr/local/bin
echo "Installation completed successfully!"
#!/bin/bash

echo "Installing dependencies..."
python3 -m pip install --quiet -r requirements.txt
echo "Running tests..."
python3 -m pytest ilogs_test.py || exit 1
echo "Compiling..."
cython ilogs.py --embed || exit 1
gcc -Os -I /usr/include/python3.7m -o kubectl-ilogs ilogs.c -lpython3.7m -lpthread -lm -lutil -ldl || exit 1
echo "Installing..."
sudo mv ./kubectl-ilogs /usr/local/bin
echo "Installation completed successfully!"
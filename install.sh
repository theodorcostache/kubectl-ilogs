#!/bin/bash

python3 -m pip install -r requirements.txt

cython ilogs.py --embed 
gcc -Os -I /usr/include/python3.7m -o kubectl-ilogs ilogs.c -lpython3.7m -lpthread -lm -lutil -ldl
sudo mv ./kubectl-ilogs /usr/local/bin
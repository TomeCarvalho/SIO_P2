#!/bin/bash

# Args
#  1: Flask application port (default: 5000)

# Setup, if necessary
source setup.sh 

# Run Flask application
cd uap

if [ $# -eq 0 ]; then
    flask run
else
    flask run --port=5001
fi
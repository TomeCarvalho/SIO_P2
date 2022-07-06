#!/bin/bash

# Args
#  1: Django application port (default: 8000)

# Setup, if necessary
source setup.sh 

# Run Django application
python3 app_sec/manage.py runserver ${1:-} 

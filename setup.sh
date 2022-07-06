#!/bin/bash

# Create venv if it doesn't exist
if ! test -d "venv"; then
	python3 -m venv venv
fi

source venv/bin/activate        # Activate venv
pip install -r requirements.txt # Install requirements
pip install cryptography --upgrade
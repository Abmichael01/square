#!/bin/bash
echo "BUILD START"
python3 -m pip install --upgrade pip  # Ensure the latest pip version
python3 -m pip install -r requirements.txt  # Install all dependencies
python3 manage.py collectstatic --noinput --clear  # Collect static files
echo "BUILD END"
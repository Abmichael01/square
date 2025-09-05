#!/bin/bash

# Build script for Vercel deployment
echo "Starting build process..."

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Collect static files
echo "Collecting static files..."
python3 manage.py collectstatic --noinput

echo "Build completed!"

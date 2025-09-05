#!/bin/bash

# Build script for Vercel deployment
echo "Starting build process..."

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Build completed!"

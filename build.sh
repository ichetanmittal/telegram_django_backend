#!/usr/bin/env bash
# exit on error
set -o errexit

# Detect Python command (works on both local and Render)
if command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    PYTHON_CMD=python3
fi

# Install dependencies
$PYTHON_CMD -m pip install -r requirements.txt

# Collect static files
$PYTHON_CMD manage.py collectstatic --no-input

# Run database migrations
$PYTHON_CMD manage.py migrate
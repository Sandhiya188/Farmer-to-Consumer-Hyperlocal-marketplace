#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

# 1. Install all dependencies from requirements.txt
pip install -r requirements.txt

# 2. Collect static files
python manage.py collectstatic --no-input

# 3. Apply database migrations
python manage.py migrate

# 4. Load full dataset (All farmers, profiles, harvests, and orders)
python manage.py loaddata seed_data

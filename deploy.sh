#!/usr/bin/env bash
set -o errexit

git pull origin main

source venv/bin/activate

pip install -r requirements.txt

python manage.py migrate

python manage.py collectstatic --no-input

sudo systemctl restart gunicorn.service

sudo systemctl reload nginx

echo "Deployment complete."
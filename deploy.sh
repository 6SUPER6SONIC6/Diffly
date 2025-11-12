#!/usr/bin/env bash
set -o errexit

echo ">>> Pulling latest code..."
git pull origin main

echo ">>> Activating virtual environment..."
source venv/bin/activate

echo ">>> Installing dependencies..."
pip install -r requirements.txt

echo ">>> Applying migrations..."
python manage.py migrate

echo ">>> Collecting static files..."
python manage.py collectstatic --no-input

echo ">>> Restarting Celery Beat..."
sudo systemctl restart celerybeat.service

echo ">>> Restarting all Celery Workers..."
for service in $(systemctl list-units --type=service --all | grep 'celeryworker@' | awk '{print $1}'); do
    echo "Restarting $service ..."
    sudo systemctl restart "$service"
done

echo ">>> Restarting Gunicorn..."
sudo systemctl restart gunicorn.service

echo ">>> Reloading Nginx..."
sudo systemctl reload nginx

echo ">>> Deployment complete."
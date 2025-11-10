import os
import subprocess
import sys

from celery import shared_task
from django.conf import settings


@shared_task
def scrape_xbox_games_task(pages=3):
    manage_py = os.path.join(settings.BASE_DIR, 'manage.py')

    cmd = [
        sys.executable,
        manage_py,
        'scrape',
        'xbox',
        'games',
        f'--pages={pages}',
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        return {"status": "success", "output": result.stdout}
    else:
        return {"status": "failure", "output": result.stdout}

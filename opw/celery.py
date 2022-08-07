from __future__ import absolute_import, unicode_literals
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'opw.settings')

app = Celery('opw')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    # 'system_sync': {
    #     'task': 'app.tasks.system_sync',
    #     'schedule': 15
    # },
    'sweeping': {
        'task': 'app.tasks.sweep',
        'schedule': 20
    }
}

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

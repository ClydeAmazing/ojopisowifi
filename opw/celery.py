from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'opw.settings')

app = Celery('opw')

app.config_from_object('django.conf:settings', namespace='CELERY')

# app.conf.beat_schedule = {
#     'pending_requests_notification_daily': {
#         'task': 'app.tasks.sweep',
#         'schedule': 15
#     }
# }

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace_api.settings')
app = Celery('marketplace_api')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks() # Discovers tasks in tasks.py of installed apps

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
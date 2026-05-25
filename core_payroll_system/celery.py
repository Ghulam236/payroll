import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_payroll_system.settings')

app = Celery('core_payroll_system')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
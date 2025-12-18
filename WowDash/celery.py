from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from kombu import Queue, Exchange

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WowDash.settings')

app = Celery('WowDash')
app.config_from_object('django.conf:settings', namespace='CELERY')

# ✅ Priority Queues
default_exchange = Exchange('default', type='direct')

app.conf.task_queues = (
    Queue('default', exchange=default_exchange, routing_key='default', priority=5),
)

# ✅ Worker Settings برای 8GB RAM
app.conf.update(
    worker_prefetch_multiplier=1,  # هر worker فقط 1 task بگیره
    worker_max_tasks_per_child=20,  # بعد 20 task، worker restart شه
    task_acks_late=False,  # ✅ تغییر به False برای جلوگیری از Duplicate
    task_reject_on_worker_lost=True,  # اگه worker مُرد، task برگرده صف
    broker_connection_retry_on_startup=True,
)

app.autodiscover_tasks()
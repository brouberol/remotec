"""
Definition of the celery worker.
"""

import os
from datetime import timedelta

from celery import Celery
from kombu import Exchange, Queue
from marathon.client import MarathonClient


class Config:
    CELERY_ACKS_LATE = True
    CELERY_TIMEZONE = 'UTC'
    CELERY_ENABLE_UTC = True
    CELERY_TASK_RESULT_EXPIRES = None
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_DEFAULT_QUEUE = 'remotec'
    CELERY_QUEUES = (
        Queue('remotec', Exchange('remotec'), routing_key='remotec'),
    )
    CELERY_INCLUDE = [
        'remotec.tasks',
    ]

cel = Celery()
cel.config_from_object(Config)
cel.conf['BROKER_URL'] = os.environ['CELERY_BROKER_URL']
cel.conf['CELERY_RESULT_BACKEND'] = os.environ['CELERY_RESULT_BACKEND']
cel.marathon = MarathonClient(
    servers=[os.environ['MARATHON_URL']],
    username=os.environ['MARATHON_USER'],
    password=os.environ['MARATHON_PASSWORD'])

cel.conf.CELERYBEAT_SCHEDULE.update({
    'drop-apps': {
        'task': 'remotec.tasks.autoremove_app',
        'schedule': timedelta(minutes=1),
        'args': ()
    },
})

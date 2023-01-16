from datetime import timedelta
import credentials

BROKER_URL = credentials.CELERY_BROKER_URL
BROKER_TRANSPORT_OPTIONS = {'fanout_prefix': True, 'fanout_patterns': True, 'visibility_timeout': 480}
CELERY_RESULT_BACKEND = BROKER_URL

CELERYBEAT_SCHEDULE = {
    'mytasl-every-15-minutes': {
        'task': 'celery_test.tasks.my_task', # notice that the complete name is needed
        'schedule': timedelta(minutes=15),
    },
}

CELERY_TIMEZONE = 'UTC'
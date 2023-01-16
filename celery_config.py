from datetime import timedelta
import credentials

BROKER_URL = credentials.CELERY_BROKER_URL
BROKER_TRANSPORT_OPTIONS = {
    "fanout_prefix": True,
    "fanout_patterns": True,
    "visibility_timeout": 480,
}
CELERY_RESULT_BACKEND = BROKER_URL

CELERYBEAT_SCHEDULE = {
    "mytask-every-15-minutes": {
        "task": "tasks.my_task",  # notice that the complete name is needed
        "schedule": timedelta(minutes=2),
    },
}

CELERY_TIMEZONE = "UTC"

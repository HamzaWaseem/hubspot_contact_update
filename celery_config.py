from celery.schedules import crontab
import credentials

CELERY_RESULT_BACKEND = credentials.CELERY_BROKER_URL

CELERYBEAT_SCHEDULE = {
    "mytask-every-15-minutes": {
        "task": "my_script.my_task",  # notice that the complete name is needed
        "schedule": crontab(minute="*/3"),
    },
}
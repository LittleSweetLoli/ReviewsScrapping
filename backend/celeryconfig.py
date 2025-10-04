from celery.schedules import crontab

beat_schedule = {
    'update-reviews-every-day': {
        'task': 'tasks.update_reviews',
        'schedule': crontab(hour=2, minute=0),  # Каждый день в 02:00 UTC
    },
}
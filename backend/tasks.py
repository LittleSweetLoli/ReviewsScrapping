from celery import Celery
from pymongo import MongoClient
from datetime import datetime
from scraper import fetch_reviews  # Ваш скрапинг-модуль
from config import Config
from celeryconfig import beat_schedule 
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация Celery
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
app = Celery('tasks', broker=redis_url, backend=redis_url)

# Настройка Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    beat_schedule=beat_schedule,
)

@app.task
def update_reviews():
    """Обновляет отзывы для всех организаций в базе."""

    logger.info("Starting reviews update")

    client = MongoClient(Config.MONGODB_URI)
    db = client['reviews_db']
    orgs = db['orgs']
    updated_count = 0
    errors = []

    for org in orgs.find():
        org_id = org['org_id']
        try:
            reviews = fetch_reviews(org_id)
            if reviews:
                orgs.update_one(
                    {'org_id': org_id},
                    {
                        '$set': {
                            'reviews': reviews,
                            'last_updated': datetime.utcnow()
                        }
                    }
                )
                updated_count += 1
            else:
                errors.append(f"No reviews found for org_id {org_id}")
        except Exception as e:
            errors.append(f"Error updating org_id {org_id}: {str(e)}")

    logger.info(f"Update completed: {updated_count} orgs, errors: {errors}")
    
    return {
        'status': 'completed',
        'updated': updated_count,
        'errors': errors
    }
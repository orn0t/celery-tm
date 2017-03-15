# Web API configuration
CELERY_TM_API_HOST = '127.0.0.1'
CELERY_TM_API_PORT = 5000

# Task schedule configuration
CELERY_TM_BROKER = 'redis://localhost:6379/0'
CELERY_TM_TIMEZONE = 'Europe/Kiev'

CELERY_TM_API_ROOT = 'http://127.0.0.1:5000'
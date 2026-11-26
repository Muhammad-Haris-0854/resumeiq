FROM resumeiq-api:local

# Same image as the API, different entrypoint: the Celery worker.
CMD ["celery", "-A", "app.workers.celery_app.celery_app", "worker", "--loglevel=INFO", "--concurrency=2", "-Q", "default,ai,ai_priority"]

from celery import Celery
from config import settings


app = Celery(
    "arxiv-data-pipeline",
    broker=settings.celery_broker_url,
    backend=settings.celery_backend_url,
)

app.config_from_object("tasks.celery_cfg")

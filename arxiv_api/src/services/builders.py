from config import settings
from celery import Celery
from clients.celery_client import CeleryClient
from arxiv_lib.vector_db.qdrant import QdrantDB
from openai import OpenAI


CELERY_BROKER_URL = settings.celery_broker_url
CELERY_BACKEND_URL = settings.celery_backend_url

openai_client = OpenAI()
celery_app = Celery(
    "arxiv-data-pipeline",
    broker=CELERY_BROKER_URL,
    backend=CELERY_BACKEND_URL,
)

celery_client = CeleryClient(celery_app)
vector_db_client = QdrantDB(settings.vectordb_host, settings.vectordb_port)

from functools import lru_cache

from arxiv_lib.vector_db.qdrant import QdrantDB
from celery import Celery
from clients.celery_client import CeleryClient
from config import settings
from openai import OpenAI


@lru_cache
def get_openai_client() -> OpenAI:
    return OpenAI()


@lru_cache
def get_celery_app() -> Celery:
    return Celery(
        "arxiv-data-pipeline",
        broker=settings.celery_broker_url,
        backend=settings.celery_backend_url,
    )


@lru_cache
def get_celery_client() -> CeleryClient:
    return CeleryClient(get_celery_app())


@lru_cache
def get_vector_db_client() -> QdrantDB:
    return QdrantDB(settings.vectordb_host, settings.vectordb_port)

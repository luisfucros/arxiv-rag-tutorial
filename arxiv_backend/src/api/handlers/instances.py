import redis
from arxiv_lib.arxiv.client import ArxivClient
from arxiv_lib.vector_db.qdrant import QdrantDB
from celery import Celery
from clients.celery_client import CeleryClient
from config import settings
from openai import OpenAI

redis_settings = settings.redis
arxiv_client = ArxivClient(settings=settings.arxiv)
redis_client = redis.Redis(
    host=redis_settings.host,
    port=redis_settings.port,
    password=redis_settings.password if redis_settings.password else None,
    db=redis_settings.db,
    decode_responses=redis_settings.decode_responses,
    socket_timeout=redis_settings.socket_timeout,
    socket_connect_timeout=redis_settings.socket_connect_timeout,
    retry_on_timeout=True,
    retry_on_error=[redis.ConnectionError, redis.TimeoutError],
)
vector_db_client = QdrantDB(settings.vectordb_host, settings.vectordb_port)
openai_client = OpenAI()

celery_app = Celery(
    "arxiv-data-pipeline",
    broker=settings.celery_broker_url,
    backend=settings.celery_backend_url,
)
celery_client = CeleryClient(celery_app)

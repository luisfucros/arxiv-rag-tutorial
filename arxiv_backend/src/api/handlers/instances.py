import redis
from arxiv_lib.arxiv.client import ArxivClient
from config import settings

arxiv_client = ArxivClient(settings=settings.arxiv)
redis_settings = settings.redis
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

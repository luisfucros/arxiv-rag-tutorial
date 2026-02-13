from arxiv_lib.arxiv.client import ArxivClient
from config import settings

arxiv_client = ArxivClient(settings=settings.arxiv)

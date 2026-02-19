import logging
from typing import List, Dict, Any, Union

from tasks.celery_app import app
from services.embeddings.fastembed import DenseEmbedding
from services.embeddings.fastembed import SparseEmbedding
from arxiv_lib.repositories.paper import PaperRepository
from arxiv_lib.tasks.enums import TaskNames
from arxiv_lib.tasks.schemas import PaperMetadataRequest, EmbeddingsRequest
from . import fetcher, database, hybrid_chunker
from config import settings

from .base import BaseTask

logger = logging.getLogger(__name__)


dense_model = DenseEmbedding()
sparse_model = SparseEmbedding()


@app.task(
    name=TaskNames.metadata_fetcher_task,
    base=BaseTask
)
def fetch_and_process_papers_task(
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Celery task wrapper for MetadataFetcher.fetch_and_process_papers

    Returns:
        Dict with db_results and vectordb_results from both processing stages
    """
    logger.info("Starting fetch_and_process_papers_task with params: %s", params)

    fetcher_params = PaperMetadataRequest(**params)

    with database.get_session() as session:  # type: ignore
        paper_repo = PaperRepository(session)

        db_results = fetcher.fetch_and_process_papers(
            paper_ids=fetcher_params.paper_ids,
            process_pdfs=fetcher_params.process_pdfs,
            store_to_db=fetcher_params.store_to_db,
            db_session=session,
        )

        logger.info("Database results: %s papers stored", db_results.get("stored", 0))

        vectordb_results = {}

        if db_results and db_results.get("stored", 0) > 0:
            papers = []

            for i in db_results["papers"]:
                arxiv_id = i.get("arxiv_id")
                if not arxiv_id:
                    continue
                papers.append(paper_repo.get_by_arxiv_id(arxiv_id))

            papers_data = []
            for paper in papers:
                if hasattr(paper, "__dict__"):
                    paper_dict = {
                        "id": str(paper.id),
                        "arxiv_id": paper.arxiv_id,
                        "title": paper.title,
                        "authors": paper.authors,
                        "abstract": paper.abstract,
                        "categories": paper.categories,
                        "published_date": paper.published_date,
                        "raw_text": paper.raw_text,
                        "sections": paper.sections,
                    }
                else:
                    paper_dict = paper
                papers_data.append(paper_dict)

            vectordb_results = hybrid_chunker.index_papers_batch(
                papers=papers_data,
                collection_name=settings.collection_name,
                replace_existing=True
            )

        return {
            "db_results": db_results,
            "vectordb_results": vectordb_results,
            "total_requested": len(fetcher_params.paper_ids)
        }


@app.task(
    name=TaskNames.embeddings_dense,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 3},
    base=BaseTask
)
def generate_dense_embedding(
    params: Dict[str, Any]
) -> Dict[str, List[List[float]]]:
    """
    Generate dense vector embeddings.
    """
    logger.info("Generating dense embeddings")
    embedding_params = EmbeddingsRequest(**params)
    text = embedding_params.text
    result = dense_model.embed(text)
    logger.info("Dense embeddings generated successfully")
    return {"embeddings": result}


@app.task(
    name=TaskNames.embeddings_sparse,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 3},
    base=BaseTask
)
def generate_sparse_embedding(
    params: Dict[str, Any]
) -> Dict[str, List[Dict[str, List[float]]]]:
    """
    Generate sparse vector embeddings.
    """
    logger.info("Generating sparse embeddings")
    embedding_params = EmbeddingsRequest(**params)
    text = embedding_params.text
    result = sparse_model.embed(text)
    logger.info("Sparse embeddings generated successfully")
    return {"sparse_embeddings": result}

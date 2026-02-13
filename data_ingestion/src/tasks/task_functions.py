from typing import List, Dict, Any, Union

from tasks.celery_app import app
from services.embeddings.fastembed import DenseEmbedding
from services.embeddings.fastembed import SparseEmbedding
from arxiv_lib.repositories.paper import PaperRepository
from . import fetcher, database, hybrid_chunker, settings
from .base import BaseTask


TextInput = Union[str, List[str]]
dense_model = DenseEmbedding()
sparse_model = SparseEmbedding()


@app.task(
    name="tasks.fetch_and_process_papers",
    base=BaseTask
)
def fetch_and_process_papers_task(
    paper_ids: List[str],
    process_pdfs: bool = True,
    store_to_db: bool = True,
) -> Dict[str, Any]:
    """
    Celery task wrapper for MetadataFetcher.fetch_and_process_papers

    Returns:
        Dict with db_results and vectordb_results from both processing stages
    """

    with database.get_session() as session:  # type: ignore
        paper_repo = PaperRepository(session)

        db_results = fetcher.fetch_and_process_papers(
            paper_ids=paper_ids,
            process_pdfs=process_pdfs,
            store_to_db=store_to_db,
            db_session=session,
        )

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
            "total_requested": len(paper_ids)
        }


@app.task(
    name="embeddings.dense",
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 3},
    base=BaseTask
)
def generate_dense_embedding(
    text: TextInput,
) -> Dict[str, List[List[float]]]:
    """
    Generate dense vector embeddings.
    """

    return {"embeddings": dense_model.embed(text)}


@app.task(
    name="embeddings.sparse",
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 3},
    base=BaseTask
)
def generate_sparse_embedding(
    text: TextInput,
) -> Dict[str, List[Dict[str, List[float]]]]:
    """
    Generate sparse vector embeddings.
    """
    return {"sparse_embeddings": sparse_model.embed(text)}

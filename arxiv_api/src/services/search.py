from dataclasses import dataclass
from typing import List, Dict, Optional
from .tasks import TaskService
from config import settings
from arxiv_lib.vector_db.qdrant import QdrantDB
from arxiv_lib.tasks.enums import TaskNames


@dataclass(frozen=True)
class SearchEngineService:
    """
    Service to handle search engine operations.
    """
    task_manager: TaskService
    vector_db_client: QdrantDB

    def search(
        self,
        query: str,
        user_id: int,
        top_k: int = 10,
        filters: Optional[Dict[str, str]] = None,
    ) -> List[Dict]:
        """
        Perform a search using the inference server to get embeddings and querying the vector DB.
        :param query: The search query text.
        :param top_k: Number of top results to return.
        :return: List of search results.
        """
        # Get embeddings for the query
        query_dense_embeddings = self.task_manager.run_task(
            TaskNames.embeddings_dense,
            {"text": [query]},
            owner_id=user_id
        )

        query_sparse_embeddings = self.task_manager.run_task(
            TaskNames.embeddings_sparse,
            {"text": [query]},
            owner_id=user_id
        )

        query_vector = {**query_sparse_embeddings, **query_dense_embeddings}

        # Query the vector database
        if settings.collection_name not in self.vector_db_client.list_collections():
            self.vector_db_client.create_collection(collection_name=settings.collection_name,
                                                    hybrid=True)
        results = self.vector_db_client.search_docs(
            collection_name=settings.collection_name,
            query_vector=query_vector,
            limit=top_k,
            hybrid=True,
            filter=filters
        )

        payloads = [result.get("payload") for result in results]

        return payloads

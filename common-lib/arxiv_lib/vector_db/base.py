from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class VectorDB(ABC):
    """Abstract base class for vector database CRUD operations."""

    @abstractmethod
    def create_collection(self, collection_name: str, **kwargs) -> None:
        """Create a new collection in the vector database.

        Args:
            collection_name: Name of the collection to create
            **kwargs: Additional parameters for collection creation
        """
        pass

    @abstractmethod
    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection from the vector database.

        Args:
            collection_name: Name of the collection to delete
        """
        pass

    @abstractmethod
    def list_collections(self) -> List[str]:
        """List all collections in the vector database.

        Returns:
            List of collection names
        """
        pass

    @abstractmethod
    def add_doc(
        self,
        collection_name: str,
        doc_id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a single document to a collection.

        Args:
            collection_name: Name of the collection
            doc_id: Unique identifier for the document
            vector: Embedding vector
            metadata: Optional metadata associated with the document
        """
        pass

    @abstractmethod
    def add_batch_docs(self, collection_name: str, docs: List[Dict[str, Any]]) -> None:
        """Add multiple documents to a collection in batch.

        Args:
            collection_name: Name of the collection
            docs: List of documents, each containing 'id', 'vector', and optional 'metadata'
        """
        pass

    @abstractmethod
    def delete_doc(self, collection_name: str, doc_id: str) -> None:
        """Delete a document from a collection.

        Args:
            collection_name: Name of the collection
            doc_id: Unique identifier of the document to delete
        """
        pass

    @abstractmethod
    def search_docs(
        self, collection_name: str, query_vector: List[float], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for similar documents in a collection.

        Args:
            collection_name: Name of the collection to search
            query_vector: Query embedding vector
            limit: Maximum number of results to return

        Returns:
            List of search results with scores and metadata
        """
        pass

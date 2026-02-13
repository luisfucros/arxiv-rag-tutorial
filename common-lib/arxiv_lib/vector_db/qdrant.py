from typing import Any, Dict, List, Optional
from zlib import crc32
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, HnswConfigDiff
from qdrant_client.http.models.models import QueryResponse
from qdrant_client import models
from qdrant_client.http.exceptions import UnexpectedResponse
from .base import VectorDB


class QdrantDB(VectorDB):
    """Qdrant vector database implementation."""

    # Configuration constants for hybrid search
    HNSW_M = 16
    HNSW_EF_CONSTRUCT = 200
    HNSW_FULL_SCAN_THRESHOLD = 10000
    HNSW_MAX_INDEXING_THREADS = 8
    SCALAR_QUANTIZATION_QUANTILE = 0.99
    DENSE_SCORE_THRESHOLD = 0.9
    FUSION_OVERSAMPLING = 2.0

    def __init__(self, host: str = "vectordb", port: int = 6333, timeout: int = 30):
        """Initialize Qdrant client with connection retry.

        Args:
            host: Host of the Qdrant server
            port: Port of the Qdrant server
            timeout: Connection timeout in seconds
        """
        try:
            self.client = QdrantClient(host=host, port=port, timeout=timeout)
        except Exception:
            raise

    def create_collection(self, collection_name: str, vector_size: int = 384,
                          distance: Distance = Distance.COSINE,
                          hybrid: bool = False,
                          **kwargs) -> None:
        """Create a new collection in Qdrant.

        Args:
            collection_name: Name of the collection to create
            vector_size: Dimensionality of the vectors
            distance: Distance metric to use (e.g., COSINE, EUCLIDEAN)
            hybrid: Whether to enable hybrid search with sparse vectors
            **kwargs: Additional parameters

        Raises:
            ValueError: If vector_size is invalid
            UnexpectedResponse: If collection creation fails
        """
        if not collection_name or not isinstance(collection_name, str):
            raise ValueError("collection_name must be a non-empty string")
        if vector_size <= 0:
            raise ValueError("vector_size must be a positive integer")

        hnsw_config = None
        quantization_config = None
        sparse_vectors_config = None

        if hybrid is True:
            hnsw_config = HnswConfigDiff(
                m=self.HNSW_M,
                ef_construct=self.HNSW_EF_CONSTRUCT,
                full_scan_threshold=self.HNSW_FULL_SCAN_THRESHOLD,
                max_indexing_threads=self.HNSW_MAX_INDEXING_THREADS,
                on_disk=False,
            )

            quantization_config = models.ScalarQuantization(
                scalar=models.ScalarQuantizationConfig(
                    type=models.ScalarType.INT8,
                    quantile=self.SCALAR_QUANTIZATION_QUANTILE,
                    always_ram=True,
                ),
            )

            sparse_vectors_config = {
                "sparse": models.SparseVectorParams(
                    index=models.SparseIndexParams(on_disk=False)
                )
            }

        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    "dense": VectorParams(size=vector_size, distance=distance),
                },
                hnsw_config=hnsw_config,
                quantization_config=quantization_config,
                sparse_vectors_config=sparse_vectors_config,
            )
        except UnexpectedResponse:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to create collection '{collection_name}': {str(e)}") from e

    @staticmethod
    def _string_to_positive_int(value: str, max_val: int = 2**31 - 1) -> int:
        """Convert string to positive integer deterministically using CRC32.

        Args:
            value: String value to convert
            max_val: Maximum value to modulo against

        Returns:
            Positive integer hash
        """
        return crc32(value.encode()) % max_val

    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection from Qdrant.

        Args:
            collection_name: Name of the collection to delete

        Raises:
            ValueError: If collection_name is invalid
            UnexpectedResponse: If deletion fails
        """
        if not collection_name or not isinstance(collection_name, str):
            raise ValueError("collection_name must be a non-empty string")

        try:
            self.client.delete_collection(collection_name=collection_name)
        except UnexpectedResponse:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to delete collection '{collection_name}': {str(e)}") from e

    def list_collections(self) -> List[str]:
        """List all collections in Qdrant.

        Returns:
            List of collection names

        Raises:
            UnexpectedResponse: If listing fails
        """
        try:
            collections = self.client.get_collections()
            collection_names = [collection.name for collection in collections.collections]
            return collection_names
        except UnexpectedResponse:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to list collections: {str(e)}") from e

    def add_doc(self, collection_name: str, doc_id: str, vector: List[float],
                metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a single document to a collection.

        Args:
            collection_name: Name of the collection
            doc_id: Unique identifier for the document
            vector: Embedding vector
            metadata: Optional metadata associated with the document

        Raises:
            ValueError: If inputs are invalid
            UnexpectedResponse: If insertion fails
        """
        if not collection_name or not isinstance(collection_name, str):
            raise ValueError("collection_name must be a non-empty string")
        if not doc_id or not isinstance(doc_id, str):
            raise ValueError("doc_id must be a non-empty string")
        if not vector or not isinstance(vector, list):
            raise ValueError("vector must be a non-empty list")

        try:
            point = PointStruct(
                id=self._string_to_positive_int(doc_id),
                vector=vector,
                payload=metadata or {},
            )
            self.client.upsert(
                collection_name=collection_name,
                points=[point],
            )
        except UnexpectedResponse:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to add document '{doc_id}': {str(e)}") from e

    def add_batch_docs(self, collection_name: str, docs: List[Dict[str, Any]],
                       hybrid: bool = False) -> None:
        """Add multiple documents to a collection in batch.

        Args:
            collection_name: Name of the collection
            docs: List of documents, each containing 'id', 'dense_embedding', and optional 'metadata'
                  Example: [{'id': 'doc1', 'dense_embedding': [...], 'metadata': {...}}, ...]
            hybrid: Whether to include sparse embeddings for hybrid search

        Returns:
            None

        Raises:
            ValueError: If inputs are invalid
            UnexpectedResponse: If batch insertion fails
        """
        if not collection_name or not isinstance(collection_name, str):
            raise ValueError("collection_name must be a non-empty string")
        if not docs or not isinstance(docs, list):
            raise ValueError("docs must be a non-empty list")

        try:
            ids = []
            dense_vectors = []
            sparse_vectors = []
            payloads = []

            for i, doc in enumerate(docs):
                doc_id = doc.get("id")
                dense_vector = doc.get("dense_embedding")
                sparse_vector = doc.get("sparse_embedding") if hybrid is True else None
                metadata = doc.get("metadata", {})

                # Validate required fields
                if not doc_id or not isinstance(doc_id, str):
                    raise ValueError(f"Document {i}: 'id' must be a non-empty string")
                if not dense_vector or not isinstance(dense_vector, list):
                    raise ValueError(f"Document {i}: 'dense_embedding' must be a non-empty list")
                if hybrid and (not sparse_vector or not isinstance(sparse_vector, dict)):
                    raise ValueError(f"Document {i}: 'sparse_embedding' required for hybrid mode")
                # if hybrid and ("indices" not in sparse_vector or "values" not in sparse_vector):
                #     raise ValueError(f"Document {i}: sparse_embedding must contain 'indices' and 'values'")

                ids.append(self._string_to_positive_int(doc_id))
                dense_vectors.append(dense_vector)
                payloads.append(metadata)
                if hybrid is True and sparse_vector is not None:
                    sparse_vectors.append(models.SparseVector(
                        indices=sparse_vector["indices"],
                        values=sparse_vector["values"],
                    ))

            # Construct vectors dictionary
            vectors_dict = {"dense": dense_vectors}
            if hybrid:
                vectors_dict["sparse"] = sparse_vectors

            self.client.upsert(
                collection_name=collection_name,
                points=models.Batch(
                    ids=ids,
                    vectors=vectors_dict,
                    payloads=payloads
                )
            )

        except UnexpectedResponse:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to add batch documents: {str(e)}") from e

    def delete_doc(self, collection_name: str, doc_id: str) -> None:
        """Delete a document from a collection.

        Args:
            collection_name: Name of the collection
            doc_id: Unique identifier of the document to delete

        Raises:
            ValueError: If inputs are invalid
            UnexpectedResponse: If deletion fails
        """
        if not collection_name or not isinstance(collection_name, str):
            raise ValueError("collection_name must be a non-empty string")
        if not doc_id or not isinstance(doc_id, str):
            raise ValueError("doc_id must be a non-empty string")

        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=[self._string_to_positive_int(doc_id)],
            )
        except UnexpectedResponse:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to delete document '{doc_id}': {str(e)}") from e

    def search_docs(self, collection_name: str, query_vector: Dict[str, Any],
                    limit: int = 10, hybrid: bool = False,
                    filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar documents in a collection.

        Args:
            collection_name: Name of the collection to search
            query_vector: Dict containing embeddings and optional sparse_embeddings
            limit: Maximum number of results to return (must be positive)
            hybrid: Whether to perform hybrid search using sparse and dense vectors
            filter: Optional metadata filter conditions

        Returns:
            List of search results with ids, scores, and payloads

        Raises:
            ValueError: If inputs are invalid
            UnexpectedResponse: If search fails
        """
        if not collection_name or not isinstance(collection_name, str):
            raise ValueError("collection_name must be a non-empty string")
        if limit <= 0:
            raise ValueError("limit must be a positive integer")
        if not query_vector or not isinstance(query_vector, dict):
            raise ValueError("query_vector must be a non-empty dict")

        filtering = self._create_filter(filter) if filter else None

        try:
            # Validate query vector structure
            if "embeddings" not in query_vector or not query_vector["embeddings"]:
                raise ValueError("query_vector must contain non-empty 'embeddings' list")

            dense_embedding = query_vector["embeddings"][0]

            if hybrid:
                if "sparse_embeddings" not in query_vector or not query_vector["sparse_embeddings"]:
                    raise ValueError("query_vector must contain 'sparse_embeddings' for hybrid search")
                sparse_embedding = query_vector["sparse_embeddings"][0]
                results = self._hybrid_search(
                    collection_name=collection_name,
                    sparse_vector=sparse_embedding,
                    dense_vector=dense_embedding,
                    query_filter=filtering,
                    limit=limit
                )
            else:
                results = self.client.query_points(
                    collection_name=collection_name,
                    query=dense_embedding,
                    using="dense",
                    query_filter=filtering,
                    limit=limit
                )

            search_results = [
                {
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload,
                }
                for result in results.points
            ]
            return search_results

        except UnexpectedResponse:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to search documents: {str(e)}") from e

    def _create_filter(self, filter_dict: Dict[str, Any]) -> models.Filter:
        """Create a Qdrant filter from a dictionary.

        Args:
            filter_dict: Dictionary of field conditions

        Returns:
            Qdrant Filter object

        Raises:
            ValueError: If filter_dict is invalid
        """
        if not filter_dict or not isinstance(filter_dict, dict):
            raise ValueError("filter_dict must be a non-empty dictionary")

        must_clauses: List[models.Condition] = [
            models.FieldCondition(
                key=key,
                match=models.MatchValue(value=value)
            )
            for key, value in filter_dict.items()
        ]
        return models.Filter(must=must_clauses)

    def _hybrid_search(
        self, collection_name: str, sparse_vector: Dict[str, Any],
        dense_vector: List[float], query_filter: Optional[models.Filter] = None,
        limit: int = 10
    ) -> QueryResponse:
        """Perform hybrid search using both sparse and dense vectors.

        Args:
            collection_name: Collection to search
            sparse_vector: Sparse embedding with 'indices' and 'values'
            dense_vector: Dense embedding vector
            query_filter: Optional Qdrant filter
            limit: Maximum results to return

        Returns:
            QueryResponse with search results

        Raises:
            ValueError: If sparse_vector format is invalid
            UnexpectedResponse: If search fails
        """
        if not sparse_vector or not isinstance(sparse_vector, dict):
            raise ValueError("sparse_vector must be a non-empty dict")
        if "indices" not in sparse_vector or "values" not in sparse_vector:
            raise ValueError("sparse_vector must contain 'indices' and 'values' keys")

        try:
            results = self.client.query_points(
                collection_name=collection_name,
                prefetch=[
                    models.Prefetch(
                        query=models.SparseVector(
                            indices=sparse_vector["indices"],
                            values=sparse_vector["values"],
                        ),
                        using="sparse",
                        limit=limit,
                    ),
                    models.Prefetch(
                        query=dense_vector,
                        using="dense",
                        score_threshold=self.DENSE_SCORE_THRESHOLD,
                        limit=limit,
                    ),
                ],
                query=models.FusionQuery(fusion=models.Fusion.RRF),
                search_params=models.SearchParams(
                    quantization=models.QuantizationSearchParams(
                        ignore=False,
                        rescore=True,
                        oversampling=self.FUSION_OVERSAMPLING,
                    ),
                ),
                query_filter=query_filter,
                limit=limit,
            )
            return results
        except UnexpectedResponse:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to perform hybrid search: {str(e)}") from e

    def content_exists(self, collection_name: str, payload: Dict[str, Any]) -> bool:
        """Check if a point with the given content already exists."""
        filter = models.Filter(
            must=[
                models.FieldCondition(
                    key=key,
                    match=models.MatchValue(value=value)
                ) for key, value in payload.items()
            ]
        )
        count_result = self.client.count(
            collection_name=collection_name,
            count_filter=filter,
            exact=True
        )
        return count_result.count > 0

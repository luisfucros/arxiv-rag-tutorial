from typing import Dict, List
from .fastembed import DenseEmbedding, SparseEmbedding


class FastembedEmbeddingsClient:
    """Client for generating embeddings using Fastembed models."""

    def __init__(self, dense_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
                 sparse_model_name: str = "prithivida/Splade_PP_en_v1"):
        self.dense_embedding_model = DenseEmbedding(model_name=dense_model_name)
        self.sparse_embedding_model = SparseEmbedding(model_name=sparse_model_name)

    def generate_dense_embeddings(self, texts: List[str]) -> List[List[int | float]]:
        """Generate dense embeddings for a list of texts.

        :param texts: List of text strings
        :returns: List of dense embeddings
        """
        return self.dense_embedding_model.embed(texts)

    def generate_sparse_embeddings(self, texts: List[str]) -> List[Dict[str, List[int | float]]]:
        """Generate sparse embeddings for a list of texts.

        :param texts: List of text strings
        :returns: List of sparse embeddings
        """
        return self.sparse_embedding_model.embed(texts)

from typing import Dict, List

from fastembed import SparseTextEmbedding, TextEmbedding

from .base import EmbeddingModel


class DenseEmbedding(EmbeddingModel):
    """Class for generating dense vector embeddings."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = TextEmbedding(model_name)

    def embed(self, text: str | List[str]) -> List[List[int | float]]:
        """
        Generate dense embeddings for the given text.

        Args:
            text: Single text string or list of text strings

        Returns:
            List of dense embeddings
        """
        embeddings_generator = self.model.embed(text)
        embeddings: List[List[int | float]] = []
        for vector in list(embeddings_generator):
            embeddings.append(vector.tolist())
        return embeddings


class SparseEmbedding(EmbeddingModel):
    """Class for generating sparse vector embeddings."""

    def __init__(self, model_name: str = "prithivida/Splade_PP_en_v1"):
        self.model = SparseTextEmbedding(model_name=model_name)

    def embed(self, text: str | List[str]) -> List[Dict[str, List[int | float]]]:
        """
        Generate sparse embeddings for the given text.

        Args:
            text: Single text string or list of text strings

        Returns:
            List of sparse embeddings
        """
        sparse_embeddings: List[Dict[str, List[int | float]]] = []
        for vector in list(self.model.embed(text)):
            sparse_vector = {"indices": vector.indices.tolist(), "values": vector.values.tolist()}
            sparse_embeddings.append(sparse_vector)
        return sparse_embeddings

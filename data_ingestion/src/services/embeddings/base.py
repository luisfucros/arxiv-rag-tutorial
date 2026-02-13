from abc import ABC, abstractmethod
from typing import Dict, List, Union


class EmbeddingModel(ABC):
    """Abstract base class for embedding models."""

    @abstractmethod
    def embed(self, text: str | List[str]) -> Union[List[List[int | float]],
                                                    List[Dict[str, List[int | float]]]]:
        """
        Generate embeddings for the given text.

        Args:
            text: Single text string or list of text strings

        Returns:
            List of embeddings
        """
        pass

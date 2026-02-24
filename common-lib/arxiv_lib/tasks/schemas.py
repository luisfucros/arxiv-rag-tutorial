from typing import List, Union

from pydantic import BaseModel, Field


class Parameters(BaseModel):
    """
    Base class for celery task parameters.
    """

    pass


class PaperMetadataRequest(Parameters):
    """
    Parameters for the metadata fetcher task.
    """

    paper_ids: List[str] = Field(..., min_length=1, max_length=20)
    process_pdfs: bool = True
    store_to_db: bool = True


class EmbeddingsRequest(Parameters):
    """
    Parameters for the embeddings tasks.
    """

    text: Union[str, List[str]]

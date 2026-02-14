from typing import Dict, Type

from . import schemas
from .enums import TaskNames


TASK_PARAMS: Dict[TaskNames, Type[schemas.Parameters]] = {
    TaskNames.metadata_fetcher_task: schemas.PaperMetadataRequest,
    TaskNames.embeddings_dense: schemas.EmbeddingsRequest,
    TaskNames.embeddings_sparse: schemas.EmbeddingsRequest
}
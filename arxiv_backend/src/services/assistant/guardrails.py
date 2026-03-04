from typing import Optional

from loguru import logger
from openai import OpenAI

from .errors import handle_openai_errors


class GuardrailService:
    """
    Soft guardrails using OpenAI moderation.
    Returns safe message if violation.
    """

    DEFAULT_MODEL = "omni-moderation-latest"

    def __init__(self, client: OpenAI, model: str = DEFAULT_MODEL):
        self.client = client
        self.model = model

    @handle_openai_errors
    def moderate_text(self, text: str) -> Optional[str]:
        """
        Returns safe message if violation, otherwise None.
        """
        try:
            response = self.client.moderations.create(
                model=self.model,
                input=text,
            )

            result = response.results[0]
            if result.flagged:
                logger.warning("Moderation flagged content: {}", result.categories)

                return (
                    "Your request violates usage policies. "
                    "I can only assist with appropriate academic-related questions "
                    "about arXiv papers."
                )

            return None

        except Exception as e:
            logger.warning("Moderation check failed, allowing content: {}", e)
            raise e

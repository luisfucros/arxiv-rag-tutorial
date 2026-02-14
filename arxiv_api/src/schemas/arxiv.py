from pydantic import BaseModel


class PaperRequest(BaseModel):
    query: str

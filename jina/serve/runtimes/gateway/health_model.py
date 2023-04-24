from pydantic import BaseModel


class JinaHealthModel(BaseModel):
    """Pydantic BaseModel for Jina health check, used as the response model in REST app."""

    ...

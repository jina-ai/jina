from typing import Optional, List

from pydantic import BaseModel

from . import PeaModel
from .custom import build_pydantic_model

PodModel = build_pydantic_model(model_name='SinglePodModel', module='pod')


class RawPodModel(BaseModel):
    head: Optional[PeaModel] = None
    tail: Optional[PeaModel] = None
    peas: List[PeaModel] = [PeaModel()]

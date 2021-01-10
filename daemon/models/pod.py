from typing import List, Optional

from pydantic import BaseModel

from .custom import build_pydantic_model

SinglePodModel = build_pydantic_model(model_name='SinglePodModel', module='pod')


class ParallelPodModel(BaseModel):
    head: Optional[SinglePodModel] = None
    tail: Optional[SinglePodModel] = None
    peas: List[SinglePodModel] = [SinglePodModel()]

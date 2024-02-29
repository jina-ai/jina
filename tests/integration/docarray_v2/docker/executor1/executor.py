from typing import Optional
from docarray import DocList, BaseDoc
from docarray.typing import NdArray
from jina import Executor, requests
import numpy as np


class MyDoc(BaseDoc):
    text: str
    embedding: Optional[NdArray] = None


class Encoder(Executor):
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

    @requests
    def encode(self, docs: DocList[MyDoc], **kwargs) -> DocList[MyDoc]:
        for doc in docs:
            doc.embedding = np.random.random(128)

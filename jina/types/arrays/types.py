from typing import (
    TypeVar,
    Sequence,
)

from ..document import Document
from ...proto import jina_pb2

DocumentArraySourceType = TypeVar(
    'DocumentArraySourceType',
    jina_pb2.DocumentArrayProto,
    Sequence[Document],
    Sequence[jina_pb2.DocumentProto],
    Document,
)

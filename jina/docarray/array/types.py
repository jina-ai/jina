from typing import (
    TypeVar,
    Sequence,
)

from ..document import Document
from ..proto import docarray_pb2

DocumentArraySourceType = TypeVar(
    'DocumentArraySourceType',
    docarray_pb2.DocumentArrayProto,
    Sequence[Document],
    Sequence[docarray_pb2.DocumentProto],
    Document,
)

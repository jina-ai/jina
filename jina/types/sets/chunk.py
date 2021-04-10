from .document import DocumentSet
from ...helper import deprecated_class
from ..lists.chunk import ChunkList

if False:
    from ..document import Document


@deprecated_class(new_class=ChunkList)
class ChunkSet(DocumentSet):
    """
    :class:`ChunkSet` is deprecated. A new class name is ChunkList.
    """

    pass

from .document import DocumentSet
from ...helper import deprecated_class
from ..arrays.chunk import ChunkArray


@deprecated_class(new_class=ChunkArray)
class ChunkSet(DocumentSet):
    """
    :class:`ChunkSet` is deprecated. A new class name is ChunkArray.
    """

    pass

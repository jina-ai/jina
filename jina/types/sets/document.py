from collections.abc import MutableSequence

from ...helper import deprecated_class

from .traversable import TraversableSequence

from ..lists.document import DocumentList

if False:
    from ..document import Document

__all__ = ['DocumentSet']


@deprecated_class(new_class=DocumentList)
class DocumentSet(TraversableSequence, MutableSequence):
    """
    :class:`DocumentSet` is deprecated. A new class name is ChunkList.
    """

    pass

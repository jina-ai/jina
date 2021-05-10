from collections.abc import MutableSequence

from ...helper import deprecated_class

from .traversable import TraversableSequence

from ..arrays.document import DocumentArray

__all__ = ['DocumentSet']


@deprecated_class(new_class=DocumentArray)
class DocumentSet(TraversableSequence, MutableSequence):
    """
    :class:`DocumentSet` is deprecated. A new class name is ChunkArray.
    """

    pass

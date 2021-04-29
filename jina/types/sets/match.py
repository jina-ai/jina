from .document import DocumentSet
from ...helper import deprecated_class

from ..arrays.match import MatchArray


@deprecated_class(new_class=MatchArray)
class MatchSet(DocumentSet):
    """
    :class:`MatchSet` is deprecated. A new class name is MatchArray.
    """

    pass

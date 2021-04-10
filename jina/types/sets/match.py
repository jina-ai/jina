from .document import DocumentSet
from ...helper import deprecated_class

from ..lists.match import MatchList

if False:
    from ..document import Document


@deprecated_class(new_class=MatchList)
class MatchSet(DocumentSet):
    """
    :class:`MatchSet` is deprecated. A new class name is MatchList.
    """

    pass

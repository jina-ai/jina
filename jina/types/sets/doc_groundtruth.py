from typing import Sequence
from .traversable import TraversableSequence
from ..lists.doc_groundtruth import DocumentGroundtruthSequence
from ...helper import deprecated_class

if False:
    from ..document.helper import DocGroundtruthPair


@deprecated_class(
    new_class=DocumentGroundtruthSequence,
    custom_msg="The class has been moved to '..types.lists', keeping its original name.",
)
class DocumentGroundtruthSequence(TraversableSequence):
    def __init__(self, pairs: Sequence['DocGroundtruthPair']):
        self._pairs = pairs

    def __iter__(self):
        yield from self._pairs

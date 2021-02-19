from typing import Sequence
from .traversable import TraversableSequence

if False:
    from ..document.helper import DocGroundtruthPair


class DocumentGroundtruthSequence(TraversableSequence):
    def __init__(self, pairs: Sequence['DocGroundtruthPair']):
        self._pairs = pairs

    def __iter__(self):
        yield from self._pairs

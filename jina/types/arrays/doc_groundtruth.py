from typing import Sequence
from .traversable import TraversableSequence

if False:
    from ..document.helper import DocGroundtruthPair


class DocumentGroundtruthSequence(TraversableSequence):
    """
    :class:`DocumentGroundtruthSequence` holds a list of `DocGrundtruthPair` objects.
    It is mostly intented to be used with Evaluators.

    :param pairs: a sequence of `DocGrundtruthPair` objects.
    """

    def __init__(self, pairs: Sequence['DocGroundtruthPair']):
        self._pairs = pairs

    def __iter__(self):
        yield from self._pairs

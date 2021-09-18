import re
import random
import operator
from collections import defaultdict
from typing import Dict, Optional, Union, Tuple, Any


if False:
    from .document import DocumentArray


class DocumentArraySearchOpsMixin:
    """ A mixin that provides search functionality to DocumentArrays"""

    def sample(self, k: int, seed: Optional[int] = None) -> 'DocumentArray':
        """random sample k elements from :class:`DocumentArray` without replacement.

        :param k: Number of elements to sample from the document array.
        :param seed: initialize the random number generator, by default is None. If set will
            save the state of the random function to produce certain outputs.
        :return: A sampled list of :class:`Document` represented as :class:`DocumentArray`.
        """

        if seed is not None:
            random.seed(seed)
        # NOTE, this could simplified to random.sample(self, k)
        # without getting indices and itemgetter etc.
        # however it's only work on DocumentArray, not DocumentArrayMemmap.
        indices = random.sample(range(len(self)), k)
        sampled = operator.itemgetter(*indices)(self)

        from .document import DocumentArray

        return DocumentArray(sampled)

    def shuffle(self, seed: Optional[int] = None) -> 'DocumentArray':
        """Randomly shuffle documents within the :class:`DocumentArray`.

        :param seed: initialize the random number generator, by default is None. If set will
            save the state of the random function to produce certain outputs.
        :return: The shuffled list of :class:`Document` represented as :class:`DocumentArray`.
        """
        from .document import DocumentArray

        return DocumentArray(self.sample(len(self), seed=seed))

    def split(self, tag: str) -> Dict[Any, 'DocumentArray']:
        """Split the `DocumentArray` into multiple DocumentArray according to the tag value of each `Document`.

        :param tag: the tag name to split stored in tags.
        :return: a dict where Documents with the same value on `tag` are grouped together, their orders
            are preserved from the original :class:`DocumentArray`.

        .. note::
            If the :attr:`tags` of :class:`Document` do not contains the specified :attr:`tag`,
            return an empty dict.
        """
        from .document import DocumentArray
        from ...helper import dunder_get

        rv = defaultdict(DocumentArray)
        for doc in self:
            if '__' in tag:
                value = dunder_get(doc.tags, tag)
            else:
                value = doc.tags.get(tag, None)

            if value is None:
                continue
            rv[value].append(doc)
        return dict(rv)

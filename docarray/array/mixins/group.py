import random
from collections import defaultdict
from typing import Dict, Any, TYPE_CHECKING, Generator

import numpy as np

if TYPE_CHECKING:
    from ..document import DocumentArray


class GroupMixin:
    """These helpers yield groups of :class:`DocumentArray` from
    a source :class:`DocumentArray` or :class:`DocumentArrayMemmap`."""

    def split(self, tag: str) -> Dict[Any, 'DocumentArray']:
        """Split the `DocumentArray` into multiple DocumentArray according to the tag value of each `Document`.

        :param tag: the tag name to split stored in tags.
        :return: a dict where Documents with the same value on `tag` are grouped together, their orders
            are preserved from the original :class:`DocumentArray`.

        .. note::
            If the :attr:`tags` of :class:`Document` do not contains the specified :attr:`tag`,
            return an empty dict.
        """
        from ..document import DocumentArray
        from ...helper import dunder_get

        rv = defaultdict(DocumentArray)
        for doc in self:
            if '__' in tag:
                value = dunder_get(doc.tags, tag)
            elif tag in doc.tags:
                value = doc.tags[tag]
            else:
                continue
            rv[value].append(doc)
        return dict(rv)

    def batch(
        self,
        batch_size: int,
        shuffle: bool = False,
    ) -> Generator['DocumentArray', None, None]:
        """
        Creates a `Generator` that yields `DocumentArray` of size `batch_size` until `docs` is fully traversed along
        the `traversal_path`. The None `docs` are filtered out and optionally the `docs` can be filtered by checking for
        the existence of a `Document` attribute.
        Note, that the last batch might be smaller than `batch_size`.

        :param batch_size: Size of each generated batch (except the last one, which might be smaller, default: 32)
        :param shuffle: If set, shuffle the Documents before dividing into minibatches.
        :yield: a Generator of `DocumentArray`, each in the length of `batch_size`
        """

        if not (isinstance(batch_size, int) and batch_size > 0):
            raise ValueError('`batch_size` should be a positive integer')

        N = len(self)
        ix = list(range(N))
        n_batches = int(np.ceil(N / batch_size))

        if shuffle:
            random.shuffle(ix)

        for i in range(n_batches):
            yield self[ix[i * batch_size : (i + 1) * batch_size]]

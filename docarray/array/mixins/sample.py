import operator
import random
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..document import DocumentArray


class SampleMixin:
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

        from ..document import DocumentArray

        return DocumentArray(sampled)

    def shuffle(self, seed: Optional[int] = None) -> 'DocumentArray':
        """Randomly shuffle documents within the :class:`DocumentArray`.

        :param seed: initialize the random number generator, by default is None. If set will
            save the state of the random function to produce certain outputs.
        :return: The shuffled list of :class:`Document` represented as :class:`DocumentArray`.
        """

        return self.sample(len(self), seed=seed)

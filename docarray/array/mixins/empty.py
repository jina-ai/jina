from typing import Type

from ...document import Document
from ...helper import T


class EmptyMixin:
    """Helper functions for building arrays with empty Document."""

    @classmethod
    def empty(cls: Type[T], size: int = 0) -> T:
        """Create a :class:`DocumentArray` or :class:`DocumentArrayMemmap` object with :attr:`size` empty
        :class:`Document` objects.

        :param size: the number of empty Documents in this container
        :return: a :class:`DocumentArray` or :class:`DocumentArrayMemmap` object
        """
        r = cls()
        r.extend(Document() for _ in range(size))
        return r

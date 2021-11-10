from typing import Union, TYPE_CHECKING

from ...document import Document

if TYPE_CHECKING:
    from ..document import DocumentArray
    from ..memmap import DocumentArrayMemmap


class EmptyMixin:
    """Helper functions for building arrays with empty Document."""

    @classmethod
    def empty(cls, size: int = 0) -> Union['DocumentArray', 'DocumentArrayMemmap']:
        """Create a :class:`DocumentArray` or :class:`DocumentArrayMemmap` object with :attr:`size` empty
        :class:`Document` objects.

        :param size: the number of empty Documents in this container
        :return: a :class:`DocumentArray` or :class:`DocumentArrayMemmap` object
        """
        r = cls()
        r.extend(Document() for _ in range(size))
        return r

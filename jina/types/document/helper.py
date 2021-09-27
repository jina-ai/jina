import functools
from typing import Iterable, List

__all__ = ['DocGroundtruthPair']

if False:
    from . import Document


class DocGroundtruthPair:
    """
    Helper class to expose common interface to the traversal logic of the BaseExecutable Driver.
    It is important to note that it checks the matching structure of `docs` and `groundtruths`. It is important while
    traversing to ensure that then the driver can be applied at a comparable level of granularity and adjacency.
    This does not imply that you can't compare at the end a document with 10 matches with a groundtruth with 20 matches

    :param doc: Target `Document`.
    :param groundtruth: The :class:`Document` with desired state.
    """

    def __init__(self, doc: 'Document', groundtruth: 'Document'):
        """Set constructor method.

        :param doc: actual Document
        :param groundtruth: groundtruth Document
        """
        self.doc = doc
        self.groundtruth = groundtruth

    @property
    def matches(self) -> Iterable['DocGroundtruthPair']:
        """Get the pairs between matches and Groundtruth.

        :yields: DocGroundtruthPair object
        """
        assert len(self.doc.matches) == len(self.groundtruth.matches)
        for doc, groundtruth in zip(self.doc.matches, self.groundtruth.matches):
            yield DocGroundtruthPair(doc, groundtruth)

    @property
    def chunks(self) -> Iterable['DocGroundtruthPair']:
        """Get the pairs between chunks and Groundtruth.

        :yields: DocGroundtruthPair object
        """
        assert len(self.doc.chunks) == len(self.groundtruth.chunks)
        for doc, groundtruth in zip(self.doc.chunks, self.groundtruth.chunks):
            yield DocGroundtruthPair(doc, groundtruth)


class VersionedMixin:
    """
    Helper class to add versioning to an object. The version number is incremented each time an attribute is set.
    """

    version = 0
    ON_GETATTR: List = []

    def _increase_version(self):
        super().__setattr__('version', self.version + 1)

    def __setattr__(self, attr, value):
        super().__setattr__(attr, value)
        self._increase_version()

    def __delattr__(self, attr):
        super(VersionedMixin, self).__delattr__(attr)
        self._increase_version()


def versioned(fn):
    """
    Decorator function that increases the version number each time the decorated method is called.
    The class of the decorated method must be a subclass of :class:`VersionedMixin`
    :param fn: the method to decorate
    :return: decorated function
    """

    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        self._increase_version()
        return fn(self, *args, **kwargs)

    return wrapper

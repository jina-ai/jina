from typing import Iterable


class Traversable:
    """
    Helper class to expose common interface to the traversal logic of the BaseExecutable Driver.
    It is important to note that it checks the matching structure of `docs` and `groundtruths`. It is important while
    traversing to ensure that then the driver can be applied at a comparable level of granularity and adjacency.
    This does not imply that you can't compare at the end a document with 10 matches with a groundtruth with 20 matches

    :param doc: Target `Document`.
    :param groundtruth: The :class:`Document` with desired state.
    """

    @property
    def matches(self) -> Iterable['Traversable']:
        """Get the pairs between matches and Groundtruth."""

    @property
    def chunks(self) -> Iterable['Traversable']:
        """Get the pairs between chunks and Groundtruth."""

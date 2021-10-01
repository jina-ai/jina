from abc import ABC, abstractmethod
from typing import Union, List, Tuple, Iterable, Iterator


if False:
    from .document import DocumentArray
    from .traversable import TraversableSequence
    from ..document import Document


class AbstractDocumentArray(ABC):
    """ Abstract class that defines the public interface of DocumentArray classes """

    @abstractmethod
    def get_attributes(self, *args, **kwargs) -> Union[List, List[List]]:
        """
        Return all nonempty values of the fields from all docs this array contains

        :param args: arguments
        :param kwargs: keyword arguments
        """
        ...

    @abstractmethod
    def get_attributes_with_docs(
        self, *args, **kwargs
    ) -> Tuple[Union[List, List[List]], 'DocumentArray']:
        """
        Returns all nonempty values of the fields together with their nonempty docs

        :param args: arguments
        :param kwargs: keyword arguments
        """
        ...

    @abstractmethod
    def traverse(self, *args, **kwargs) -> Iterable['TraversableSequence']:
        """
        Returns an Iterator of :class:``TraversableSequence`` of the leaves when applying the traversal_paths.
        Each :class:``TraversableSequence`` is either the root Documents, a ChunkArray or a MatchArray.

        :param args: arguments
        :param kwargs: keyword arguments
        """
        ...

    @abstractmethod
    def traverse_flat_per_path(
        self, *args, **kwargs
    ) -> Iterable['TraversableSequence']:
        """
        Returns a flattened :class:``TraversableSequence`` per path.

        :param args: arguments
        :param kwargs: keyword arguments
        """
        ...

    @abstractmethod
    def traverse_flat(self, *args, **kwargs) -> 'TraversableSequence':
        """
        Returns a single flattened :class:``TraversableSequence`` with all Documents, that are reachable by traversal
        paths.

        :param args: arguments
        :param kwargs: keyword arguments
        """
        ...

    @abstractmethod
    def match(self, *args, **kwargs) -> None:
        """Computes embedding-based nearest neighbour in another document array for each Document in `self`,
        and store results in the `matches` attribute of each Document.

        :param args: arguments
        :param kwargs: keyword arguments
        """
        ...

    @abstractmethod
    def visualize(self, *args, **kwargs):
        """Visualizes embeddings in a 2D projection with the PCA algorithm. This function requires ``matplotlib``
        installed.

        :param args: arguments
        :param kwargs: keyword arguments
        """
        ...

    @abstractmethod
    def sample(self, *args, **kwargs) -> 'DocumentArray':
        """
        Randomly sample k elements from  the document array without replacement.

        :param args: arguments
        :param kwargs: keyword arguments
        """
        ...

    @abstractmethod
    def shuffle(self, *args, **kwargs) -> 'DocumentArray':
        """
        Randomly shuffle documents within the document array.

        :param args: arguments
        :param kwargs: keyword arguments
        """
        ...

    @abstractmethod
    def __eq__(self):
        ...

    @abstractmethod
    def __len__(self):
        ...

    @abstractmethod
    def __iter__(self) -> Iterator['Document']:
        ...

    @abstractmethod
    def __contains__(self):
        ...

    @abstractmethod
    def __getitem__(self, item: Union[int, str, slice]):
        ...

    @abstractmethod
    def __setitem__(self, key, value: 'Document'):
        ...

    @abstractmethod
    def __delitem__(self, index: Union[int, str, slice]):
        ...

    @abstractmethod
    def extend(self, *args, **kwargs) -> None:
        """
        Extend the document array by appending all the items from the iterable.

        :param args: arguments
        :param kwargs: keyword arguments
        """
        ...

    @abstractmethod
    def append(self, *args, **kwargs):
        """
        Append the Document to the document array.

        :param args: arguments
        :param kwargs: keyword arguments
        """
        ...

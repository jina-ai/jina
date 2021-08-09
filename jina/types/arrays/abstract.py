import re
from abc import ABC, abstractmethod
from math import inf
from typing import Union, List, Tuple, Iterable, Callable, Optional, Dict, Iterator

import numpy as np

if False:
    from .document import DocumentArray
    from .memmap import DocumentArrayMemmap
    from .traversable import TraversableSequence
    from ..document import Document


class AbstractDocumentArray(ABC):
    """ Abstract class that defines the public interface of DocumentArray classes """

    @abstractmethod
    def get_attributes(self, *fields: str) -> Union[List, List[List]]:
        """Return all nonempty values of the fields from all docs this array contains

        :param fields: Variable length argument with the name of the fields to extract
        """
        ...

    @abstractmethod
    def get_attributes_with_docs(
        self,
        *fields: str,
    ) -> Tuple[Union[List, List[List]], 'DocumentArray']:
        """Return all nonempty values of the fields together with their nonempty docs

        :param fields: Variable length argument with the name of the fields to extract
        """
        ...

    @abstractmethod
    def traverse(
        self, traversal_paths: Iterable[str]
    ) -> Iterable['TraversableSequence']:
        """
        Return an Iterator of :class:``TraversableSequence`` of the leaves when applying the traversal_paths.
        Each :class:``TraversableSequence`` is either the root Documents, a ChunkArray or a MatchArray.

        :param traversal_paths: a list of string that represents the traversal path
        """
        ...

    @abstractmethod
    def traverse_flat_per_path(
        self, traversal_paths: Iterable[str]
    ) -> Iterable['TraversableSequence']:
        """
        Returns a flattened :class:``TraversableSequence`` per path in :param:``traversal_paths``
        with all Documents, that are reached by the path.

        :param traversal_paths: a list of string that represents the traversal path
        """
        ...

    @abstractmethod
    def traverse_flat(self, traversal_paths: Iterable[str]) -> 'TraversableSequence':
        """
        Returns a single flattened :class:``TraversableSequence`` with all Documents, that are reached
        via the :param:``traversal_paths``.

        .. warning::
            When defining the :param:``traversal_paths`` with multiple paths, the returned
            :class:``Documents`` are determined at once and not on the fly. This is a different
            behavior then in :method:``traverse`` and :method:``traverse_flattened_per_path``!

        :param traversal_paths: a list of string that represents the traversal path
        """
        ...

    @abstractmethod
    def match(
        self,
        darray: Union['DocumentArray', 'DocumentArrayMemmap'],
        metric: Union[
            str, Callable[['np.ndarray', 'np.ndarray'], 'np.ndarray']
        ] = 'cosine',
        limit: Optional[int] = inf,
        normalization: Optional[Tuple[int, int]] = None,
        use_scipy: bool = False,
        metric_name: Optional[str] = None,
    ) -> None:
        """Compute embedding based nearest neighbour in `another` for each Document in `self`,
        and store results in `matches`.

        .. note::
            'cosine', 'euclidean', 'sqeuclidean' are supported natively without extra dependency.

            You can use other distance metric provided by ``scipy``, such as ‘braycurtis’, ‘canberra’, ‘chebyshev’,
            ‘cityblock’, ‘correlation’, ‘cosine’, ‘dice’, ‘euclidean’, ‘hamming’, ‘jaccard’, ‘jensenshannon’,
            ‘kulsinski’, ‘mahalanobis’, ‘matching’, ‘minkowski’, ‘rogerstanimoto’, ‘russellrao’, ‘seuclidean’,
            ‘sokalmichener’, ‘sokalsneath’, ‘sqeuclidean’, ‘wminkowski’, ‘yule’.

            To use scipy metric, please set ``use_scipy=True``.

        - To make all matches values in [0, 1], use ``dA.match(dB, normalization=(0, 1))``
        - To invert the distance as score and make all values in range [0, 1],
            use ``dA.match(dB, normalization=(1, 0))``. Note, how ``normalization`` differs from the previous.

        :param darray: the other DocumentArray or DocumentArrayMemmap to match against
        :param metric: the distance metric
        :param limit: the maximum number of matches, when not given
                      all Documents in `another` are considered as matches
        :param normalization: a tuple [a, b] to be used with min-max normalization,
                                the min distance will be rescaled to `a`, the max distance will be rescaled to `b`
                                all values will be rescaled into range `[a, b]`.
        :param use_scipy: use Scipy as the computation backend
        :param metric_name: if provided, then match result will be marked with this string.
        """
        ...

    @abstractmethod
    def visualize(
        self,
        output: Optional[str] = None,
        title: Optional[str] = None,
        colored_tag: Optional[str] = None,
        colormap: str = 'rainbow',
        method: str = 'pca',
        show_axis: bool = False,
    ):
        """Visualize embeddings in a 2D projection with the PCA algorithm. This function requires ``matplotlib`` installed.

        If `tag_name` is provided the plot uses a distinct color for each unique tag value in the
        documents of the DocumentArray.

        :param output: Optional path to store the visualization. If not given, show in UI
        :param title: Optional title of the plot. When not given, the default title is used.
        :param colored_tag: Optional str that specifies tag used to color the plot
        :param colormap: the colormap string supported by matplotlib.
        :param method: the visualization method, available `pca`, `tsne`. `pca` is fast but may not well represent
                nonlinear relationship of high-dimensional data. `tsne` requires scikit-learn to be installed and is
                much slower.
        :param show_axis: If set, axis and bounding box of the plot will be printed.

        """
        ...

    @abstractmethod
    def find(
        self,
        regexes: Dict[str, Union[str, re.Pattern]],
        traversal_paths: Tuple[str] = ('r',),
        operator: str = '>=',
        threshold: Optional[int] = None,
    ) -> 'DocumentArray':
        """
        Find Documents whose tag match the regular expressions in `regexes`.
        If `regexes` contain several regular expressions an `operator` can be used to
        specify a decision depending on the of regular expression matches specified by `value`.

        The supported operators are: ['<', '>', '==', '!=', '<=', '>=']

        Example: If `len(regexes)=3` then the documents from the DocumentArray will be accepted if
                 they match all 3 regular expressions.

        Example: If `len(regexes)=3`,  `value=2` and `operator='>='` then the documents
                 from the DocumentArray will be accepted if they match at least 2 regular expressions.

        :param regexes: Dictionary of the form {tag: Optional[str, regex]}
        :param traversal_paths: List specifying traversal paths
        :param operator: Operator used to accept/reject a document
        :param threshold: Number of regex that should match the operator to accept a Document.
                          If no value is provided `threshold=len(regexes)`.
        """
        ...

    @abstractmethod
    def sample(self, k: int, seed: Optional[int] = None) -> 'DocumentArray':
        """random sample k elements from :class:`DocumentArray` without replacement.

        :param k: Number of elements to sample from the document array.
        :param seed: initialize the random number generator, by default is None. If set will
            save the state of the random function to produce certain outputs.
        """
        ...

    @abstractmethod
    def shuffle(self, seed: Optional[int] = None) -> 'DocumentArray':
        """Randomly shuffle documents within the :class:`DocumentArray`.

        :param seed: initialize the random number generator, by default is None. If set will
            save the state of the random function to produce certain outputs.
        """
        ...

    @abstractmethod
    def __eq__(self, other):
        ...

    @abstractmethod
    def __len__(self):
        ...

    @abstractmethod
    def __iter__(self) -> Iterator['Document']:
        ...

    @abstractmethod
    def __contains__(self, item: str):
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
    def extend(self, iterable: Iterable['Document']) -> None:
        """Extend the :class:`DocumentArrayMemmap` by appending all the items from the iterable.

        :param iterable: the iterable of Documents to extend this array with
        """
        ...

    @abstractmethod
    def append(self, doc: 'Document', **kwargs):
        """
        Append :param:`doc` in :class:`DocumentArrayMemmap`.

        :param doc: The doc needs to be appended.
        :param kwargs: keyword args
        """
        ...

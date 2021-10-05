from abc import abstractmethod
from typing import Iterable, Sequence, TYPE_CHECKING, Optional, Generator

if TYPE_CHECKING:
    from .document import DocumentArray
    from ..document import Document


def _check_traversal_path_type(tp):
    if not (
        tp
        and not isinstance(tp, str)
        and isinstance(tp, Sequence)
        and all(isinstance(p, str) for p in tp)
    ):
        raise TypeError('`traversal_paths` needs to be `Sequence[str]`')


class TraversableSequence:
    """
    A mixin used for traversing a `Sequence[Traversable]`.
    """

    def traverse(
        self, traversal_paths: Sequence[str]
    ) -> Iterable['TraversableSequence']:
        """
        Return an Iterator of :class:``TraversableSequence`` of the leaves when applying the traversal_paths.
        Each :class:``TraversableSequence`` is either the root Documents, a ChunkArray or a MatchArray.

        :param traversal_paths: a list of string that represents the traversal path
        :yield: :class:``TraversableSequence`` of the leaves when applying the traversal_paths.

        Example on ``traversal_paths``:

            - [`r`]: docs in this TraversableSequence
            - [`m`]: all match-documents at adjacency 1
            - [`c`]: all child-documents at granularity 1
            - [`cc`]: all child-documents at granularity 2
            - [`mm`]: all match-documents at adjacency 2
            - [`cm`]: all match-document at adjacency 1 and granularity 1
            - [`r`, `c`]: docs in this TraversableSequence and all child-documents at granularity 1

        """
        _check_traversal_path_type(traversal_paths)

        for p in traversal_paths:
            yield from self._traverse(self, p)

    @staticmethod
    def _traverse(docs: 'TraversableSequence', path: str):
        if path:
            loc = path[0]
            if loc == 'r':
                yield from TraversableSequence._traverse(docs, path[1:])
            elif loc == 'm':
                for d in docs:
                    yield from TraversableSequence._traverse(d.matches, path[1:])
            elif loc == 'c':
                for d in docs:
                    yield from TraversableSequence._traverse(d.chunks, path[1:])
            else:
                raise ValueError(
                    f'`path`:{loc} is invalid, must be one of `c`, `r`, `m`'
                )
        else:
            yield docs

    def traverse_flat_per_path(self, traversal_paths: Sequence[str]):
        """
        Returns a flattened :class:``TraversableSequence`` per path in :param:``traversal_paths``
        with all Documents, that are reached by the path.

        :param traversal_paths: a list of string that represents the traversal path
        :yield: :class:``TraversableSequence`` containing the document of all leaves per path.
        """
        _check_traversal_path_type(traversal_paths)

        for p in traversal_paths:
            yield self._flatten(self._traverse(self, p))

    def traverse_flat(self, traversal_paths: Sequence[str]) -> Iterable['Document']:
        """
        Returns a single flattened :class:``TraversableSequence`` with all Documents, that are reached
        via the :param:``traversal_paths``.

        .. warning::
            When defining the :param:``traversal_paths`` with multiple paths, the returned
            :class:``Documents`` are determined at once and not on the fly. This is a different
            behavior then in :method:``traverse`` and :method:``traverse_flattened_per_path``!

        :param traversal_paths: a list of string that represents the traversal path
        :return: a single :class:``TraversableSequence`` containing the document of all leaves when applying the traversal_paths.
        """
        _check_traversal_path_type(traversal_paths)

        leaves = self.traverse(traversal_paths)
        return self._flatten(leaves)

    def batch(
        self,
        batch_size: int,
        traversal_paths: Sequence[str] = None,
        require_attr: Optional[str] = None,
    ) -> Generator['DocumentArray', None, None]:
        """
        Creates a `Generator` that yields `DocumentArray` of size `batch_size` until `docs` is fully traversed along
        the `traversal_path`. The None `docs` are filtered out and optionally the `docs` can be filtered by checking for
        the existence of a `Document` attribute.
        Note, that the last batch might be smaller than `batch_size`.

        :param traversal_paths: Specifies along which "axis" the document shall be traversed. (defaults to ['r'])
        :param batch_size: Size of each generated batch (except the last one, which might be smaller, default: 32)
        :param require_attr: Optionally, you can filter out docs which don't have this attribute
        :yield: a Generator of `DocumentArray`, each in the length of `batch_size`
        """

        if not (isinstance(batch_size, int) and batch_size > 0):
            raise ValueError('`batch_size` should be a positive integer')

        if traversal_paths:
            _check_traversal_path_type(traversal_paths)
            docs = self.traverse_flat(traversal_paths)
        else:
            docs = self

        from .document import DocumentArray

        _batch = DocumentArray()
        for d in docs:
            # For array-valued attributes we need to compare to None
            if require_attr in ['embedding', 'blob']:
                if getattr(d, require_attr) is not None:
                    _batch.append(d)
            elif require_attr is not None:
                if getattr(d, require_attr):
                    _batch.append(d)
            else:
                _batch.append(d)

            if len(_batch) == batch_size:
                yield _batch
                _batch = DocumentArray()

        if _batch:
            yield _batch

    @staticmethod
    @abstractmethod
    def _flatten(sequence):
        ...

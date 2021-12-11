import warnings
from abc import abstractmethod
from typing import (
    Iterable,
    Sequence,
    TYPE_CHECKING,
    Optional,
    Callable,
    Union,
)

if TYPE_CHECKING:
    from ..document import DocumentArray
    from ...document import Document
    from ...helper import T


def _check_traversal_path_type(tp):
    if isinstance(tp, str):
        return tp
    elif isinstance(tp, Sequence) and all(isinstance(p, str) for p in tp):
        tp = ','.join(tp)
        warnings.warn(
            f'The syntax of traversal_path is changed to comma-separated string, '
            f'that means your need to change {tp} into `{",".join(tp)}`. '
            f'The old list of string syntax will be deprecated soon',
            DeprecationWarning,
        )
        return tp
    else:
        raise TypeError(
            '`traversal_paths` needs to be a string of comma-separated paths'
        )


class TraverseMixin:
    """
    A mixin used for traversing :class:`DocumentArray` or :class:`DocumentArrayMemmap`.
    """

    def traverse(
        self: 'T',
        traversal_paths: str,
        filter_fn: Optional[Callable[['Document'], bool]] = None,
    ) -> Iterable['T']:
        """
        Return an Iterator of :class:``TraversableSequence`` of the leaves when applying the traversal_paths.
        Each :class:``TraversableSequence`` is either the root Documents, a ChunkArray or a MatchArray.

        :param traversal_paths: a comma-separated string that represents the traversal path
        :param filter_fn: function to filter docs during traversal
        :yield: :class:``TraversableSequence`` of the leaves when applying the traversal_paths.

        Example on ``traversal_paths``:

            - `r`: docs in this TraversableSequence
            - `m`: all match-documents at adjacency 1
            - `c`: all child-documents at granularity 1
            - `cc`: all child-documents at granularity 2
            - `mm`: all match-documents at adjacency 2
            - `cm`: all match-document at adjacency 1 and granularity 1
            - `r,c`: docs in this TraversableSequence and all child-documents at granularity 1

        """
        traversal_paths = _check_traversal_path_type(traversal_paths)

        for p in traversal_paths.split(','):
            yield from self._traverse(self, p, filter_fn=filter_fn)

    @staticmethod
    def _traverse(
        docs: 'T',
        path: str,
        filter_fn: Optional[Callable[['Document'], bool]] = None,
    ):
        if path:
            loc = path[0]
            if loc == 'r':
                yield from TraverseMixin._traverse(docs, path[1:], filter_fn=filter_fn)
            elif loc == 'm':
                for d in docs:
                    yield from TraverseMixin._traverse(
                        d.matches, path[1:], filter_fn=filter_fn
                    )
            elif loc == 'c':
                for d in docs:
                    yield from TraverseMixin._traverse(
                        d.chunks, path[1:], filter_fn=filter_fn
                    )
            else:
                raise ValueError(
                    f'`path`:{loc} is invalid, must be one of `c`, `r`, `m`'
                )
        elif filter_fn is None:
            yield docs
        else:
            from ..document import DocumentArray

            yield DocumentArray(list(filter(filter_fn, docs)))

    def traverse_flat_per_path(
        self,
        traversal_paths: str,
        filter_fn: Optional[Callable[['Document'], bool]] = None,
    ):
        """
        Returns a flattened :class:``TraversableSequence`` per path in ``traversal_paths``
        with all Documents, that are reached by the path.

        :param traversal_paths: a comma-separated string that represents the traversal path
        :param filter_fn: function to filter docs during traversal
        :yield: :class:``TraversableSequence`` containing the document of all leaves per path.
        """
        traversal_paths = _check_traversal_path_type(traversal_paths)

        for p in traversal_paths.split(','):
            yield self._flatten(self._traverse(self, p, filter_fn=filter_fn))

    def traverse_flat(
        self,
        traversal_paths: str,
        filter_fn: Optional[Callable[['Document'], bool]] = None,
    ) -> Union['DocumentArray', Iterable['Document']]:
        """
        Returns a single flattened :class:``TraversableSequence`` with all Documents, that are reached
        via the ``traversal_paths``.

        .. warning::
            When defining the ``traversal_paths`` with multiple paths, the returned
            :class:``Documents`` are determined at once and not on the fly. This is a different
            behavior then in :method:``traverse`` and :method:``traverse_flattened_per_path``!

        :param traversal_paths: a list of string that represents the traversal path
        :param filter_fn: function to filter docs during traversal
        :return: a single :class:``TraversableSequence`` containing the document of all leaves when applying the traversal_paths.
        """
        traversal_paths = _check_traversal_path_type(traversal_paths)
        if traversal_paths == 'r' and filter_fn is None:
            return self

        leaves = self.traverse(traversal_paths, filter_fn=filter_fn)
        return self._flatten(leaves)

    def flatten(self, copy: bool = True) -> 'DocumentArray':
        """Flatten all nested chunks and matches into one :class:`DocumentArray`.

        .. note::
            Flatten an already flattened DocumentArray will have no effect.

        .. warning::
            DocumentArrayMemmap do not support `copy=False`.

        :param copy: copy the document (DAM only supports copy=True), otherwise returns a view of the original
        :return: a flattened :class:`DocumentArray` object.
        """
        from ..document import DocumentArray

        def _yield_all():
            for d in self:
                yield from _yield_nest(d)

        def _yield_nest(doc: 'Document'):
            from ...document import Document

            for d in doc.chunks:
                yield from _yield_nest(d)
            for m in doc.matches:
                yield from _yield_nest(m)

            if copy:
                d = Document(doc, copy=True)
                d.chunks.clear()
                d.matches.clear()
                yield d
            else:
                doc.matches.clear()
                doc.chunks.clear()
                yield doc

        return DocumentArray(_yield_all())

    @staticmethod
    @abstractmethod
    def _flatten(sequence):
        ...

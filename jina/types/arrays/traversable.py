import itertools
from typing import Iterable


def _check_traversal_path_type(traversal_paths):
    if isinstance(traversal_paths, str):
        raise ValueError('traversal_paths needs to be an Iterable[str]')


class TraversableSequence:
    """
    A mixin used for traversing a `Sequence[Traversable]`.
    """

    def traverse(
        self, traversal_paths: Iterable[str]
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

    def traverse_flat_per_path(
        self, traversal_paths: Iterable[str]
    ) -> Iterable['TraversableSequence']:
        """
        Returns a flattened :class:``TraversableSequence`` per path in :param:``traversal_paths``
        with all Documents, that are reached by the path.

        :param traversal_paths: a list of string that represents the traversal path
        :yield: :class:``TraversableSequence`` containing the document of all leaves per path.
        """
        _check_traversal_path_type(traversal_paths)

        for p in traversal_paths:
            yield self._flatten(self._traverse(self, p))

    def traverse_flat(self, traversal_paths: Iterable[str]) -> 'TraversableSequence':
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

    @classmethod
    def _flatten(cls, sequence):
        return cls(list(itertools.chain.from_iterable(sequence)))

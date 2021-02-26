from typing import Iterable
import itertools

if False:
    from ..document.traversable import Traversable


class TraversableSequence:
    """
    A mixin used for traversing a `Sequence[Traversable]`.
    """

    def __iter__(self) -> Iterable['Traversable']:
        raise NotImplementedError

    def traverse(self, traversal_paths: Iterable[str]) -> Iterable['TraversableSequence']:
        """
        Return an Iterator of :class:``TraversableSequence`` of the leaves when applying the traversal_paths.
        Each :class:``TraversableSequence`` is either the root Documents, a ChunkSet or a MatchSet.

        :param traversal_paths: a list of string that represents the traversal path
        :return: an Iterator of :class:``TraversableSequence`` of the leaves when applying the traversal_paths.

        Example on ``traversal_paths``:

            - [`r`]: docs in this TraversableSequence
            - [`m`]: all match-documents at adjacency 1
            - [`c`]: all child-documents at granularity 1
            - [`cc`]: all child-documents at granularity 2
            - [`mm`]: all match-documents at adjacency 2
            - [`cm`]: all match-document at adjacency 1 and granularity 1
            - [`r`, `c`]: docs in this TraversableSequence and all child-documents at granularity 1

        """

        def _traverse(docs: 'TraversableSequence', path: str):
            if path:
                loc = path[0]
                if loc == 'r':
                    yield from _traverse(docs, path[1:])
                elif loc == 'm':
                    for d in docs:
                        yield from _traverse(d.matches, path[1:])
                elif loc == 'c':
                    for d in docs:
                        yield from _traverse(d.chunks, path[1:])
            else:
                yield docs

        def _traverse_all():
            for p in traversal_paths:
                yield from _traverse(self, p)

        return _traverse_all()

    def traverse_flatten(self, traversal_paths: Iterable[str]) -> 'TraversableSequence':
        """
        Returns a single flattened :class:``TraversableSequence`` with all Documents, that are reached
        via the :param:``traversal_paths``.

        :param traversal_paths: a list of string that represents the traversal path
        :return: a singel :class:``TraversableSequence`` containing the document of all leaves when applying the traversal_paths.
        """
        leaves = self.traverse(traversal_paths)
        return self._flatten(leaves)

    @classmethod
    def _flatten(cls, sequence):
        return cls(list(itertools.chain.from_iterable(sequence)))

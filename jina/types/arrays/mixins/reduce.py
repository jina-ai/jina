import heapq
from collections import defaultdict
from typing import List, TYPE_CHECKING, Optional, Callable, Dict

if TYPE_CHECKING:
    from ..document import DocumentArray
    from ...document import Document
    from ....helper import T


class ReduceMixin:
    """A mixing that provides reducing logic for :class:`DocumentArray` or :class:`DocumentArrayMemmap`"""

    @classmethod
    def _merge_sorted(cls, das: List['DocumentArray'], key: Callable):
        return cls(heapq.merge(*das, key=key))

    def reduce(self: 'T', da: 'T'):
        """
        Reduces da and the current DocumentArray into one DocumentArray in-place. Changes are applied to the current
        DocumentArray
        :param da: DocumentArray
        """
        self._reduce(da)

    def _reduce(self: 'T', da: 'T', unmerged_matches: Optional[Dict] = None):
        """
        Reduces da and the current DocumentArray into one DocumentArray in-place. Changes are applied to the current
            DocumentArray
        :param da: DocumentArray
        :param unmerged_matches: If set, matches will be assumed to be sorted and will be added to `unsorted_matches`
            in order to be merged in a sorted order later
        """
        for doc in da:
            if doc.id in self:
                self._reduce_doc(self[doc.id], doc, unmerged_matches=unmerged_matches)
            else:
                self.append(doc)

    @staticmethod
    def _reduce_doc(
        doc1: 'Document', doc2: 'Document', unmerged_matches: Optional[Dict] = None
    ):
        """
        Reduces doc1 and doc2 into one Document in-place. Changes are applied to doc1
        :param doc1: first Document
        :param doc2: second Document
        :param unmerged_matches: If set, matches will be assumed to be sorted and will be added to `unsorted_matches`
            in order to be merged in a sorted order later
        """
        if unmerged_matches is not None:
            unmerged_matches[doc1.id].extend([doc1.matches, doc2.matches])
        else:
            if len(doc2.matches) > 0:
                doc1.matches._reduce(doc2.matches)

        if len(doc2.chunks) > 0:
            doc1.chunks._reduce(doc2.chunks)

    def reduce_mat(
        self: 'T', da_matrix: List['T'], sort_key: Optional[Callable] = None
    ) -> 'T':
        """
        Reduces a list of DocumentArrays and this  DocumentArray into one DocumentArray. Changes are applied to this
            DocumentArray
        :param da_matrix: List of DocumentArray to be reduced
        :param sort_key: If set, matches will be assumed to be sorted and will be merged in a sorted order using
            sorted_key
        :return: the resulting DocumentArray
        """
        if sort_key:
            unmerged_matches = defaultdict(list)
            for da in da_matrix:
                self._reduce(da, unmerged_matches=unmerged_matches)

            for key, matches_matrix in unmerged_matches.items():
                sorted_matches = self._merge_sorted(matches_matrix, key=sort_key)
                matches_matrix[0].clear()
                matches_matrix[0].extend(sorted_matches)

        else:
            for da in da_matrix:
                self._reduce(da)

        return self

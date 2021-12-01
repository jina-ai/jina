from typing import List, TYPE_CHECKING


if TYPE_CHECKING:
    from ..document import DocumentArray
    from ...document import Document
    from ....helper import T


def _merge_mat_dac(da_matrix: List['DocumentArray']) -> 'DocumentArray':
    if len(da_matrix) == 2:
        da_matrix[0].merge(da_matrix[1])
        return da_matrix[0]
    elif len(da_matrix) == 1:
        return da_matrix[0]

    else:
        length = len(da_matrix)
        da1 = _merge_mat_dac(da_matrix[: int(length / 2)])
        da2 = _merge_mat_dac(da_matrix[int(length / 2) + 1 :])
        da1.merge(da2)
        return da1


class ReduceMixin:
    """A mixing that provides reducing logic for :class:`DocumentArray` or :class:`DocumentArrayMemmap`"""

    def merge(self: 'T', da: 'T'):
        """
        Merges da into the current DocumentArray in-place
        :param da: DocumentArray
        """
        for doc in da:
            if doc.id in self:
                self.merge_doc(self[doc.id], doc)
            else:
                self.append(doc)

    @staticmethod
    def _merge_doc(doc1: 'Document', doc2: 'Document'):
        """
        Merges doc1 into doc2 in-place
        :param doc1: first Document
        :param doc2: second Document
        """
        if len(doc2.matches) > 0:
            doc1.matches.merge(doc2.matches)

        if len(doc2.chunks) > 0:
            doc1.chunks.merge(doc2.chunks)

    def merge_mat(self: 'T', da_matrix: List['T']) -> 'T':
        """
        Merges a list of DocumentArrays into this  DocumentArray
        :param da_matrix: List of DocumentArray to be merged
        :return: the resulting DocumentArray
        """
        for da in da_matrix:
            self.merge(da)
        return self

    def merge_mat_dac(self: 'T', da_matrix: List['DocumentArray']) -> 'DocumentArray':
        """
        Merges a list of DocumentArrays into this  DocumentArray following the divide and conquer strategy
        :param da_matrix: List of DocumentArray to be merged
        :return: the resulting DocumentArray
        """
        return _merge_mat_dac([self] + da_matrix)

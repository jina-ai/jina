from typing import List, TYPE_CHECKING


if TYPE_CHECKING:
    from ..document import DocumentArray
    from ...document import Document
    from ....helper import T


def _reduce_mat_dac(da_matrix: List['DocumentArray']) -> 'DocumentArray':
    if len(da_matrix) == 2:
        da_matrix[0].reduce(da_matrix[1])
        return da_matrix[0]
    elif len(da_matrix) == 1:
        return da_matrix[0]

    else:
        length = len(da_matrix)
        da1 = _reduce_mat_dac(da_matrix[: int(length / 2)])
        da2 = _reduce_mat_dac(da_matrix[int(length / 2) :])
        da1.reduce(da2)
        return da1


class ReduceMixin:
    """A mixing that provides reducing logic for :class:`DocumentArray` or :class:`DocumentArrayMemmap`"""

    def reduce(self: 'T', da: 'T'):
        """
        Reduces da and the current DocumentArray into one DocumentArray in-place. Changes are applied to the current
        DocumentArray
        :param da: DocumentArray
        """
        for doc in da:
            if doc.id in self:
                self._reduce_doc(self[doc.id], doc)
            else:
                self.append(doc)

    @staticmethod
    def _reduce_doc(doc1: 'Document', doc2: 'Document'):
        """
        Reduces doc1 and doc2 into one Document in-place. Changes are applied to doc1
        :param doc1: first Document
        :param doc2: second Document
        """
        if len(doc2.matches) > 0:
            doc1.matches.reduce(doc2.matches)

        if len(doc2.chunks) > 0:
            doc1.chunks.reduce(doc2.chunks)

    def reduce_mat(self: 'T', da_matrix: List['T']) -> 'T':
        """
        Reduces a list of DocumentArrays and this  DocumentArray into one DocumentArray. Changes are applied to this
        DocumentArray
        :param da_matrix: List of DocumentArray to be reduced
        :return: the resulting DocumentArray
        """
        for da in da_matrix:
            self.reduce(da)
        return self

    def reduce_mat_dac(self: 'T', da_matrix: List['DocumentArray']) -> 'DocumentArray':
        """
        Reduces a list of DocumentArrays into this  DocumentArray following the divide and conquer strategy
        :param da_matrix: List of DocumentArray to be reduced
        :return: the resulting DocumentArray
        """
        return _reduce_mat_dac([self] + da_matrix)

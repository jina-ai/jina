from typing import List

from jina import Document, DocumentArray


def merge(da1: DocumentArray, da2: DocumentArray):
    """
    Merges da2 into da1 in-place
    :param da1: first DocumentArray
    :param da2: second DocumentArray
    """
    for doc2 in da2:
        if doc2.id in da1:
            merge_doc(da1[doc2.id], doc2)
        else:
            da1.append(doc2)


def merge_doc(doc1: Document, doc2: Document):
    """
    Merges doc1 into doc2 in-place
    :param doc1: first Document
    :param doc2: second Document
    """
    if len(doc2.matches) > 0:
        merge(doc1.matches, doc2.matches)

    if len(doc2.chunks) > 0:
        merge(doc1.chunks, doc2.chunks)


def merge_mat(da_matrix: List[DocumentArray]) -> DocumentArray:
    """
    Merges a list of DocumentArrays and stores the result in the first DocumentArray
    :param da_matrix: List of DocumentArray to be merged into one DocumentArray
    :return: the resulting DocumentArray
    """
    res_da = da_matrix[0]
    for da in da_matrix[1:]:
        merge(res_da, da)
    return res_da


def merge_mat_dac(da_matrix: List[DocumentArray]) -> DocumentArray:
    """
    Merges a list of DocumentArrays following the devide and conquer strategy
    :param da_matrix: List of DocumentArray to be merged into one DocumentArray
    :return: the resulting DocumentArray
    """
    if len(da_matrix) == 2:
        merge(da_matrix[0], da_matrix[1])
        return da_matrix[0]
    elif len(da_matrix) == 1:
        return da_matrix[0]

    else:
        length = len(da_matrix)
        da1 = merge_mat_dac(da_matrix[: int(length / 2)])
        da2 = merge_mat_dac(da_matrix[int(length / 2) + 1 :])
        merge(da1, da2)
        return da1

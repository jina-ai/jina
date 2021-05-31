from typing import Optional, Iterator, Tuple, Dict

import numpy as np

from . import Document, DocumentSourceType
from ..struct import StructView
from ..ndarray.sparse.scipy import SparseNdArray

__all__ = ['GraphDocument']

if False:
    from scipy.sparse import coo_matrix


class GraphDocument(Document):
    """
    :class:`GraphDocument` is a data type created based on Jina primitive data type :class:`Document`.

    It adds functionality that lets you work with a `Document` as a `graph` where all its chunks are the nodes in the `graph`.

    It exposes functionality to access and manipulate `graph related info` from the `DocumentProto` such as adjacency and edge features.

    .. warning::
        - It assumes that every ``chunk`` of a ``document`` is a node of a graph.
        - It assumes that every :class:`MultimodalDocument` have at least two chunks.
        - Build :class:`MultimodalDocument` from :attr:`modality_content_mapping` expects you assign
          :attr:`Document.content` as the value of the dictionary.

    :param document: the document to construct from. If ``bytes`` is given
            then deserialize a :class:`DocumentProto`; ``dict`` is given then
            parse a :class:`DocumentProto` from it; ``str`` is given, then consider
            it as a JSON string and parse a :class:`DocumentProto` from it; finally,
            one can also give `DocumentProto` directly, then depending on the ``copy``,
            it builds a view or a copy from it.
    :param copy: when ``document`` is given as a :class:`DocumentProto` object, build a
            view (i.e. weak reference) from it or a deep copy from it.
    :param kwargs: further key value arguments
    """

    def __init__(
        self,
        document: Optional[DocumentSourceType] = None,
        copy: bool = False,
        **kwargs,
    ):
        super().__init__(document=document, copy=copy, **kwargs)
        self._chunk_offset_to_chunk_index = {
            chunk.id: offset for offset, chunk in enumerate(self.chunks)
        }

    def add_edge(
        self, doc1: 'Document', doc2: 'Document', features: Optional[Dict] = None
    ):
        """
        Add an edge to the graph connecting `doc1` with `doc2`

        :param doc1: the starting node for this edge
        :param doc2: the ending node for this edge
        :param features: Optional features dictionary to be added to this new created edge
        """
        for doc in {doc1, doc2}:
            if doc.id not in self._chunk_offset_to_chunk_index:
                self.chunks.append(doc)
                self._chunk_offset_to_chunk_index[doc.id] = len(self.chunks)
        current_adjacency = self.adjacency
        row = current_adjacency.row
        col = current_adjacency.col
        data = current_adjacency.data
        row = np.append(row, self._chunk_offset_to_chunk_index[doc1.id])
        col = np.append(col, self._chunk_offset_to_chunk_index[doc2.id])
        data = np.append(data, 1)
        self.adjacency = coo_matrix(
            (data, (row, col)), shape=(len(self.chunks), len(self.chunks))
        )
        if features is not None:
            self.edge_features[len(self.adjacency)] = features

    @property
    def edge_features(self):
        """
        The dictionary of edge features, indexed by `edge_id` in the `edge list`

        .. # noqa: DAR201
        """
        return StructView(self._pb_body.graph_info.edge_features)

    @edge_features.setter
    def edge_features(self, value: Dict):
        """Set the `edge_features` field of this Graph to a Python dict

        :param value: a Python dict
        """
        self._pb_body.graph_info.edge_features.Clear()
        self._pb_body.graph_info.edge_features.update(value)

    @property
    def adjacency(self):
        """
        The adjacency list for this graph,

        .. # noqa: DAR201
        """
        return SparseNdArray(self._pb_body.graph_info.adjacency, sp_format='coo').value

    @adjacency.setter
    def adjacency(self, value: 'coo_matrix'):
        """
        Set the adjacency list of this graph.

        :param value: the float weight of the document.
        """
        from ... import JINA_GLOBAL

        if JINA_GLOBAL.scipy_installed:
            SparseNdArray(
                self._pb_body.graph_info.adjacency, sp_format='coo'
            ).value = value

    def __iter__(self) -> Iterator[Tuple['Document']]:
        for (row, col) in self.adjacency:
            yield self.chunks[row], self.chunks[col]

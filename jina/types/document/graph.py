from typing import Optional, Iterator, Tuple, Dict, Iterable

import numpy as np

from . import Document, DocumentSourceType
from ..arrays import ChunkArray
from ..ndarray.sparse.scipy import SparseNdArray
from ..struct import StructView
from ...importer import ImportExtensions
from ...logging.predefined import default_logger

__all__ = ['GraphDocument']

if False:
    from scipy.sparse import coo_matrix
    from dgl import DGLGraph


class GraphDocument(Document):
    """
    :class:`GraphDocument` is a data type created based on Jina primitive data type :class:`Document`.

    It adds functionality that lets you work with a `Document` as a `directed graph` where all its chunks are the nodes in the `graph`.

    It exposes functionality to access and manipulate `graph related info` from the `DocumentProto` such as adjacency and edge features.

    .. warning::
        - It assumes that every ``chunk`` of a ``document`` is a node of a graph.

    :param document: the document to construct from. If ``bytes`` is given
            then deserialize a :class:`DocumentProto`; ``dict`` is given then
            parse a :class:`DocumentProto` from it; ``str`` is given, then consider
            it as a JSON string and parse a :class:`DocumentProto` from it; finally,
            one can also give `DocumentProto` directly, then depending on the ``copy``,
            it builds a view or a copy from it.
    :param copy: when ``document`` is given as a :class:`DocumentProto` object, build a
            view (i.e. weak reference) from it or a deep copy from it.
    :param force_undirected: indicates if the actual `proto` object represented by this `GraphDocument` must be updated to set its
            `undirected` property to `True`. Otherwise, the value providing by the `document` source or the default value is mantained.
            This parameter is called `force_undirected` and not `undirected` to make sure that if a `valid` `DocumentSourceType` is provided
            with an `undirected` flag set, it can be respected and not silently overriden by a missleading default. This is specially needed
            when a `GraphDocument` is distributed to `Executors`.
    :param kwargs: further key value arguments
    """

    def __init__(
        self,
        document: Optional[DocumentSourceType] = None,
        copy: bool = False,
        force_undirected: bool = False,
        **kwargs,
    ):
        self._check_installed_array_packages()
        super().__init__(document=document, copy=copy, **kwargs)
        self._node_id_to_offset = {
            node.id: offset for offset, node in enumerate(self.nodes)
        }  # dangerous because document is stateless, try to work only with proto
        if force_undirected:
            self._pb_body.graph.undirected = force_undirected

    @staticmethod
    def _check_installed_array_packages():
        from ... import JINA_GLOBAL

        if JINA_GLOBAL.scipy_installed is None:
            JINA_GLOBAL.scipy_installed = False
            with ImportExtensions(
                required=True,
                pkg_name='scipy',
                help_text=f'GraphDocument requires scipy to be installed for sparse matrix support.',
            ):
                JINA_GLOBAL.scipy_installed = True

    def add_node(self, node: 'Document'):
        """
        Add a a node to the graph

        :param node: the node to be added to the graph
        """
        if node.id in self._node_id_to_offset:
            default_logger.debug(f'Document {node.id} is already a node of the graph')
            return

        self._node_id_to_offset[node.id] = len(self.nodes)
        self.nodes.append(node)

    def remove_node(self, node: 'Document'):
        """
        Remove a node from the graph along with the edges that may contain it

        :param node: the node to be removed from the graph
        """
        from scipy.sparse import coo_matrix

        if node.id not in self._node_id_to_offset:
            default_logger.debug(
                f'Trying to remove document {node.id} from the graph while is not a node of the graph'
            )
            return

        offset = self._node_id_to_offset[node.id]

        if self.num_edges > 0:
            edges_to_remove = []
            for edge_id, (row, col) in enumerate(
                zip(self.adjacency.row, self.adjacency.col)
            ):
                if row.item() == offset or col.item() == offset:
                    edge_features_keys = (
                        f'{self.nodes[row.item()].id}-{self.nodes[col.item()]}'
                    )
                    edges_to_remove.append((edge_id, edge_features_keys))

            for edge_id, edge_features_key in reversed(edges_to_remove):
                self._remove_edge_id(edge_id, edge_features_key)

            if self.num_edges > 0:
                row = np.copy(self.adjacency.row)
                col = np.copy(self.adjacency.col)
                data = np.copy(self.adjacency.data)
                for i in range(self.num_edges):
                    if self.adjacency.row[i] > offset:
                        row[i] = row[i] - 1
                    if self.adjacency.col[i] > offset:
                        col[i] = col[i] - 1
                SparseNdArray(
                    self._pb_body.graph.adjacency, sp_format='coo'
                ).value = coo_matrix((data, (row, col)))

        del self.nodes[offset]
        self._node_id_to_offset = {
            node.id: offset for offset, node in enumerate(self.nodes)
        }

    def _get_edge_key(self, doc1: 'Document', doc2: 'Document') -> str:
        """
        Create a key that is lexicographically sorted in the case of undirected graphs

        :param doc1: the starting node for this edge
        :param doc2: the ending node for this edge
        :return: lexicographically sorted key where doc1 < doc2 if undirected
        """

        if self.undirected:
            return (
                f'{doc1.id}-{doc2.id}' if doc1.id < doc2.id else f'{doc2.id}-{doc1.id}'
            )
        else:
            return f'{doc1.id}-{doc2.id}'

    def add_edge(
        self, doc1: 'Document', doc2: 'Document', features: Optional[Dict] = None
    ):
        """
        Add an edge to the graph connecting `doc1` with `doc2`

        :param doc1: the starting node for this edge
        :param doc2: the ending node for this edge
        :param features: Optional features dictionary to be added to this new created edge
        """
        from scipy.sparse import coo_matrix

        edge_key = self._get_edge_key(doc1, doc2)

        if edge_key not in self.edge_features:
            self.edge_features[edge_key] = features
            self.add_node(doc1)
            self.add_node(doc2)

            current_adjacency = self.adjacency

            source_id = doc1.id
            target_id = doc2.id
            if self.undirected and doc1.id > doc2.id:
                source_id = doc2.id
                target_id = doc1.id

            source_node_offset = self._node_id_to_offset[source_id]
            target_node_offset = self._node_id_to_offset[target_id]
            row = (
                np.append(current_adjacency.row, source_node_offset)
                if current_adjacency is not None
                else np.array([source_node_offset])
            )
            col = (
                np.append(current_adjacency.col, target_node_offset)
                if current_adjacency is not None
                else np.array([target_node_offset])
            )
            data = (
                np.append(current_adjacency.data, 1)
                if current_adjacency is not None
                else np.array([1])
            )

            SparseNdArray(
                self._pb_body.graph.adjacency, sp_format='coo'
            ).value = coo_matrix((data, (row, col)))

    def _remove_edge_id(self, edge_id: int, edge_feature_key: str):
        from scipy.sparse import coo_matrix

        if self.adjacency is not None:
            if edge_id > self.num_edges:
                raise Exception(
                    f'Trying to remove edge {edge_id} while number of edges is {self.num_edges}'
                )
            row = np.delete(self.adjacency.row, edge_id)
            col = np.delete(self.adjacency.col, edge_id)
            data = np.delete(self.adjacency.data, edge_id)
            if row.shape[0] > 0:
                SparseNdArray(
                    self._pb_body.graph.adjacency, sp_format='coo'
                ).value = coo_matrix((data, (row, col)))
            else:
                SparseNdArray(
                    self._pb_body.graph.adjacency, sp_format='coo'
                ).value = coo_matrix((0, 0))

            if edge_feature_key in self.edge_features:
                del self.edge_features[edge_feature_key]

    def remove_edge(self, doc1: 'Document', doc2: 'Document'):
        """
        Remove the edge between doc1 and doc2 from the graph

        :param doc1: the starting node for this edge
        :param doc2: the ending node for this edge
        """
        offset1 = self._node_id_to_offset[doc1.id]
        offset2 = self._node_id_to_offset[doc2.id]
        for edge_id, (row, col) in enumerate(
            zip(self.adjacency.row, self.adjacency.col)
        ):
            if row.item() == offset1 and col.item() == offset2:
                edge_key = self._get_edge_key(doc1, doc2)
                self._remove_edge_id(edge_id, edge_key)

    @property
    def edge_features(self) -> StructView:
        """
        The dictionary of edge features, indexed by `edge_id` in the `edge list`

        .. # noqa: DAR201
        """
        return StructView(self._pb_body.graph.edge_features)

    @property
    def adjacency(self) -> SparseNdArray:
        """
        The adjacency list for this graph.

        .. # noqa: DAR201
        """
        return SparseNdArray(self._pb_body.graph.adjacency, sp_format='coo').value

    @property
    def undirected(self) -> bool:
        """
        The undirected flag of this graph.

        .. # noqa: DAR201
        """
        return self._pb_body.graph.undirected

    @property
    def num_nodes(self) -> int:
        """
        The number of nodes in the graph

        .. # noqa: DAR201
        """
        return len(self.nodes)

    @property
    def num_edges(self) -> int:
        """
        The number of edges in the graph

        .. # noqa: DAR201
        """
        adjacency = self.adjacency
        return adjacency.data.shape[0] if adjacency is not None else 0

    @property
    def nodes(self) -> ChunkArray:
        """
        The nodes list for this graph

        .. # noqa: DAR201
        """
        return self.chunks

    def get_out_degree(self, doc: 'Document') -> int:
        """
        The out degree of the doc node

        .. # noqa: DAR201
        :param doc: the document node from which to extract the outdegree.
        """
        out_edges = self.get_outgoing_nodes(doc)
        return len(out_edges) if out_edges else 0

    def get_in_degree(self, doc: 'Document') -> int:
        """
        The in degree of the doc node

        .. # noqa: DAR201
        :param doc: the document node from which to extract the indegree.
        """
        in_edges = self.get_incoming_nodes(doc)
        return len(in_edges) if in_edges else 0

    @nodes.setter
    def nodes(self, value: Iterable['Document']):
        """Set all nodes of the current document.

        :param value: the array of nodes of this document
        """
        self.chunks = value

    def get_outgoing_nodes(self, doc: 'Document') -> Optional[ChunkArray]:
        """
        Get all the outgoing edges from `doc`

        .. # noqa: DAR201
        :param doc: the document node from which to extract the outgoing nodes.
        """
        if self.adjacency is not None and doc.id in self._node_id_to_offset:
            offset = self._node_id_to_offset[doc.id]
            return ChunkArray(
                [
                    self.nodes[col.item()]
                    for (row, col) in zip(self.adjacency.row, self.adjacency.col)
                    if row.item() == offset
                ],
                reference_doc=self,
            )

    def get_incoming_nodes(self, doc: 'Document') -> Optional[ChunkArray]:
        """
        Get all the outgoing edges from `doc`

        .. # noqa: DAR201
        :param doc: the document node from which to extract the incoming nodes.
        """
        if self.adjacency is not None and doc.id in self._node_id_to_offset:
            offset = self._node_id_to_offset[doc.id]
            return ChunkArray(
                [
                    self.nodes[row.item()]
                    for (row, col) in zip(self.adjacency.row, self.adjacency.col)
                    if col.item() == offset
                ],
                reference_doc=self,
            )

    @staticmethod
    def load_from_dgl_graph(dgl_graph: 'DGLGraph') -> 'GraphDocument':
        """
        Construct a GraphDocument from of graph with type `DGLGraph`

        .. # noqa: DAR201
        :param dgl_graph: the graph from which to construct a `GraphDocument`.

        .. warning::
            - This method only deals with the graph structure (nodes and conectivity) graph
                features that are task specific  are ignored.
            - This method has no way to know id the origin `dgl_graph` is an undirected graph, and therefore
              the property `undirected` will by `False` by default. If you want you can set the property manually.
        """
        jina_graph = GraphDocument()
        nodeid_to_doc = {}
        for node in dgl_graph.nodes():
            node_doc = Document()
            nodeid_to_doc[int(node)] = node_doc
            jina_graph.add_node(node_doc)

        for node_source, node_destination in zip(*dgl_graph.edges()):
            jina_graph.add_edge(
                nodeid_to_doc[int(node_source)], nodeid_to_doc[int(node_destination)]
            )

        return jina_graph

    def to_dgl_graph(self) -> 'DGLGraph':
        """
        Construct a  `dgl.DGLGraph` from a `GraphDocument` instance.

        .. warning::
        - This method only deals with the graph structure (nodes and conectivity) graph
          features that are task specific are ignored.

        .. # noqa: DAR201
        """
        from ... import JINA_GLOBAL

        if JINA_GLOBAL.dgl_installed is None:
            JINA_GLOBAL.dgl_installed = False
            with ImportExtensions(
                required=True,
                pkg_name='dgl',
                help_text=f'to_dgl_graph method requires dgl to be installed',
            ):
                import dgl

                JINA_GLOBAL.dgl_installed = True

        if JINA_GLOBAL.torch_installed is None:
            JINA_GLOBAL.torch_installed = False
            with ImportExtensions(
                required=True,
                pkg_name='torch',
                help_text=f'to_dgl_graph method requires torch to be installed',
            ):
                import torch

                JINA_GLOBAL.torch_installed = True

        import torch
        import dgl

        if self.adjacency is None:
            default_logger.debug(
                f'Trying to convert to dgl graph without \
                                  for GraphDocument.id = {self.id} without adjacency matrix'
            )
            dgl_graph = dgl.DGLGraph()
            dgl_graph.add_nodes(self.num_nodes)
            return dgl_graph
        else:
            rows = self.adjacency.row.copy()
            cols = self.adjacency.col.copy()

            if self.undirected:
                source_nodes = torch.tensor(np.concatenate((rows, cols)))
                destination_nodes = torch.tensor(np.concatenate((cols, rows)))
            else:
                source_nodes = torch.tensor(rows)
                destination_nodes = torch.tensor(cols)

            return dgl.graph((source_nodes, destination_nodes))

    def __iter__(self) -> Iterator[Tuple['Document']]:
        if self.adjacency is not None:
            for (row, col) in zip(self.adjacency.row, self.adjacency.col):
                yield self.nodes[row.item()], self.nodes[col.item()]
        else:
            default_logger.debug(f'Trying to iterate over a graph without edges')

    def __mermaid_str__(self) -> str:

        if len(self.nodes) == 0:
            return super().__mermaid_str__()

        results = []
        printed_ids = set()
        _node_id_node_mermaid_id = {}

        for node in self.nodes:
            _node_id_node_mermaid_id[node.id] = node._mermaid_id

        for in_node, out_node in self:

            in_node_mermaid_id = _node_id_node_mermaid_id[in_node.id]
            if in_node_mermaid_id not in printed_ids:
                in_node._mermaid_id = in_node_mermaid_id
                printed_ids.add(in_node_mermaid_id)
                results.append(in_node.__mermaid_str__())

            out_node_mermaid_id = _node_id_node_mermaid_id[out_node.id]
            if out_node_mermaid_id not in printed_ids:
                out_node._mermaid_id = out_node_mermaid_id
                printed_ids.add(out_node_mermaid_id)
                results.append(out_node.__mermaid_str__())

            if self.undirected:
                results.append(f'{in_node_mermaid_id[:3]} -- {out_node_mermaid_id[:3]}')
            else:
                results.append(
                    f'{in_node_mermaid_id[:3]} --> {out_node_mermaid_id[:3]}'
                )

        return '\n'.join(results)

import pytest

import numpy as np

from jina import Executor, requests, DocumentArray, Document, Flow
from jina.types.document.graph import GraphDocument
from tests import validate_callback


class GraphExecutor(Executor):
    @requests
    def node_and_graph_encode(self, docs: DocumentArray, **kwargs):
        """
        This executor is going to add for each node an embedding computed as the sum of outgoing and incoming edges.
        Then is going to assign a graph embedding as the sum of the embeddings of all its nodes multiplied by the `feature` weight of each edge.

        .. # noqa: DAR201
        :param docs: Array of GraphDocuments
        """
        for doc in docs:
            graph = GraphDocument(doc)
            for node in graph.nodes:
                node.embedding = np.array(
                    [graph.get_out_degree(node) + graph.get_in_degree(node)]
                )

            sum = 0
            for node in graph.nodes:
                node_embedding = node.embedding[0]
                for out_node in graph.get_outgoing_nodes(node):
                    node_embedding = (
                        node_embedding
                        * graph.edge_features[f'{node.id}-{out_node.id}']['weight']
                    )
                for in_node in graph.get_incoming_nodes(node):
                    node_embedding = (
                        node_embedding
                        * graph.edge_features[f'{in_node.id}-{node.id}']['weight']
                    )
                sum += node_embedding
            graph.embedding = np.array([sum])


@pytest.fixture()
def graph():
    graph = GraphDocument()

    doc0 = Document(text='Document0')
    doc1 = Document(text='Document1')
    doc2 = Document(text='Document2')
    doc3 = Document(text='Document3')

    graph.add_edge(doc0, doc1, features={'weight': 1})
    graph.add_edge(doc0, doc2, features={'weight': 1})
    graph.add_edge(doc2, doc1, features={'weight': 10})
    graph.add_edge(doc1, doc3, features={'weight': 1})
    graph.add_edge(doc2, doc3, features={'weight': 1})
    return graph


def test_flow_with_graph_executor(graph, mocker):
    def validate_resp(resp):
        assert len(resp.data.docs) == 1
        for doc in resp.data.docs:
            graph = GraphDocument(doc)
            assert graph.embedding[0] == 64
            assert len(graph.nodes) == 4
            for i, node in enumerate(graph.nodes):
                if i == 0:
                    assert node.embedding[0] == 2
                if i == 1:
                    assert node.embedding[0] == 3
                if i == 2:
                    assert node.embedding[0] == 3
                if i == 3:
                    assert node.embedding[0] == 2

    mock = mocker.Mock()

    with Flow().add(uses=GraphExecutor) as flow:
        flow.index(inputs=DocumentArray([graph]), on_done=mock)

    validate_callback(mock, validate_resp)

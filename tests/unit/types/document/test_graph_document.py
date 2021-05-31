import pytest

from jina.types.document.graph import GraphDocument
from jina.types.document import Document


@pytest.fixture()
def graph():
    graph = GraphDocument()

    doc0 = Document(text='Document0')
    doc1 = Document(text='Document1')
    doc2 = Document(text='Document2')
    doc3 = Document(text='Document3')

    graph.add_edge(doc0, doc1)
    graph.add_edge(doc0, doc2)
    graph.add_edge(doc2, doc1)
    graph.add_edge(doc1, doc3)
    graph.add_edge(doc2, doc3)
    return graph


def validate_graph(graph):
    doc0 = graph.chunks[0]
    assert doc0.text == 'Document0'
    doc1 = graph.chunks[1]
    assert doc1.text == 'Document1'
    doc2 = graph.chunks[2]
    assert doc2.text == 'Document2'
    doc3 = graph.chunks[3]
    assert doc3.text == 'Document3'

    assert len(graph.nodes) == 4

    assert len(graph) == 5
    for i, (d1, d2) in enumerate(graph):
        if i == 0:
            assert d1.text == 'Document0'
            assert d2.text == 'Document1'
        if i == 1:
            assert d1.text == 'Document0'
            assert d2.text == 'Document2'
        if i == 2:
            assert d1.text == 'Document2'
            assert d2.text == 'Document1'
        if i == 3:
            assert d1.text == 'Document1'
            assert d2.text == 'Document3'
        if i == 4:
            assert d1.text == 'Document2'
            assert d2.text == 'Document3'

    outgoing_0 = graph.get_outgoing_nodes(doc0)
    assert len(outgoing_0) == 2
    assert outgoing_0[0].text == 'Document1'
    assert outgoing_0[1].text == 'Document2'

    incoming_0 = graph.get_incoming_nodes(doc0)
    assert len(incoming_0) == 0

    outgoing_1 = graph.get_outgoing_nodes(doc1)
    assert len(outgoing_1) == 1
    assert outgoing_1[0].text == 'Document3'

    incoming_1 = graph.get_incoming_nodes(doc1)
    assert len(incoming_1) == 2
    assert incoming_1[0].text == 'Document0'
    assert incoming_1[1].text == 'Document2'

    outgoing_2 = graph.get_outgoing_nodes(doc2)
    assert len(outgoing_2) == 2
    assert outgoing_2[0].text == 'Document1'
    assert outgoing_2[1].text == 'Document3'

    incoming_2 = graph.get_incoming_nodes(doc2)
    assert len(incoming_2) == 1
    assert incoming_2[0].text == 'Document0'

    outgoing_3 = graph.get_outgoing_nodes(doc3)
    assert len(outgoing_3) == 0

    incoming_3 = graph.get_incoming_nodes(doc3)
    assert len(incoming_3) == 2
    assert incoming_3[0].text == 'Document1'
    assert incoming_3[1].text == 'Document2'

    assert graph.get_incoming_nodes(Document()) is None
    assert graph.get_outgoing_nodes(Document()) is None


def test_graph_document_add_edges(graph):
    validate_graph(graph)


def test_graph_document_from_graph(graph):
    graph2 = GraphDocument(graph)
    validate_graph(graph2)


def test_graph_document_from_proto(graph):
    graph2 = GraphDocument(graph._pb_body)
    validate_graph(graph2)

import pytest
import numpy as np

from jina.flow import Flow
from jina.proto import jina_pb2
from jina.types.ndarray.generic import NdArray

random_np_array = np.random.randint(10, size=(50, 10))
buffer = 'text_buffer'.encode()
text = 'text_content'


@pytest.fixture
def input_doc_with_chunks():
    doc = jina_pb2.DocumentProto()
    doc.tags['id'] = 1
    chunk0 = doc.chunks.add()
    chunk0.tags['id'] = 10
    chunk0.text = text
    NdArray(chunk0.embedding).value = random_np_array
    chunk1 = doc.chunks.add()
    chunk1.tags['id'] = 20
    NdArray(chunk1.blob).value = random_np_array
    chunk2 = doc.chunks.add()
    chunk2.tags['id'] = 30
    chunk2.buffer = buffer
    return doc


def test_message_docs_different_chunk_types(input_doc_with_chunks, mocker):
    def validate_chunks_fn(resp):
        mock()
        assert len(resp.search.docs) == 1
        doc = resp.search.docs[0]
        assert int(doc.tags['id']) == 1
        assert len(doc.chunks) == 3

        chunk0 = doc.chunks[0]
        assert int(chunk0.tags['id']) == 10
        assert chunk0.text == text
        np.testing.assert_almost_equal(random_np_array, NdArray(chunk0.embedding).value)

        chunk1 = doc.chunks[1]
        assert int(chunk1.tags['id']) == 20
        np.testing.assert_almost_equal(random_np_array, NdArray(chunk1.blob).value)

        chunk2 = doc.chunks[2]
        assert int(chunk2.tags['id']) == 30
        assert chunk2.buffer == buffer

    mock = mocker.Mock()

    with Flow().add() as f:
        f.search(input_fn=[input_doc_with_chunks], on_done=validate_chunks_fn)

    mock.assert_called_once()


@pytest.fixture
def input_doc_with_matches():
    doc = jina_pb2.DocumentProto()
    doc.tags['id'] = 1
    match0 = doc.matches.add()
    match0.tags['id'] = 10
    match0.text = text
    NdArray(match0.embedding).value = random_np_array
    match1 = doc.matches.add()
    match1.tags['id'] = 20
    NdArray(match1.blob).value = random_np_array
    match2 = doc.matches.add()
    match2.tags['id'] = 30
    match2.buffer = buffer
    return doc


def test_message_docs_different_matches_types(input_doc_with_matches, mocker):
    def validate_matches_fn(resp):
        mock()
        assert len(resp.search.docs) == 1
        doc = resp.search.docs[0]
        assert int(doc.tags['id']) == 1
        assert len(doc.matches) == 3

        match0 = doc.matches[0]
        assert int(match0.tags['id']) == 10
        assert match0.text == text
        np.testing.assert_almost_equal(random_np_array, NdArray(match0.embedding).value)

        match1 = doc.matches[1]
        assert int(match1.tags['id']) == 20
        np.testing.assert_almost_equal(random_np_array, NdArray(match1.blob).value)

        match2 = doc.matches[2]
        assert int(match2.tags['id']) == 30
        assert match2.buffer == buffer

    mock = mocker.Mock()
    with Flow().add() as f:
        f.search(input_fn=[input_doc_with_matches], on_done=validate_matches_fn)
    mock.assert_called_once()


@pytest.fixture
def input_doc_chunks_and_matches():
    doc = jina_pb2.DocumentProto()
    doc.tags['id'] = 1
    chunk0 = doc.chunks.add()
    chunk0.tags['id'] = 10
    chunk0.text = text
    NdArray(chunk0.embedding).value = random_np_array
    chunk1 = doc.chunks.add()
    chunk1.tags['id'] = 20
    NdArray(chunk1.blob).value = random_np_array
    chunk2 = doc.chunks.add()
    chunk2.tags['id'] = 30
    chunk2.buffer = buffer
    match0 = doc.matches.add()
    match0.tags['id'] = 10
    match0.text = text
    NdArray(match0.embedding).value = random_np_array
    match1 = doc.matches.add()
    match1.tags['id'] = 20
    NdArray(match1.blob).value = random_np_array
    match2 = doc.matches.add()
    match2.tags['id'] = 30
    match2.buffer = buffer
    return doc


def test_message_docs_different_chunks_and_matches_types(input_doc_chunks_and_matches, mocker):
    def validate_chunks_and_matches_fn(resp):
        assert len(resp.search.docs) == 1
        doc = resp.search.docs[0]
        assert int(doc.tags['id']) == 1
        assert len(doc.chunks) == 3

        chunk0 = doc.chunks[0]
        assert int(chunk0.tags['id']) == 10
        assert chunk0.text == text
        np.testing.assert_almost_equal(random_np_array, NdArray(chunk0.embedding).value)

        chunk1 = doc.chunks[1]
        assert int(chunk1.tags['id']) == 20
        np.testing.assert_almost_equal(random_np_array, NdArray(chunk1.blob).value)

        chunk2 = doc.chunks[2]
        assert int(chunk2.tags['id']) == 30
        assert chunk2.buffer == buffer

        assert len(doc.matches) == 3

        match0 = doc.matches[0]
        assert int(match0.tags['id']) == 10
        assert match0.text == text
        np.testing.assert_almost_equal(random_np_array, NdArray(match0.embedding).value)

        match1 = doc.matches[1]
        assert int(match1.tags['id']) == 20
        np.testing.assert_almost_equal(random_np_array, NdArray(match1.blob).value)

        match2 = doc.matches[2]
        assert int(match2.tags['id']) == 30
        assert match2.buffer == buffer

    response_mock = mocker.Mock(wrap=validate_chunks_and_matches_fn)

    with Flow().add() as f:
        f.search(input_fn=[input_doc_chunks_and_matches], on_done=response_mock)

    response_mock.assert_called()

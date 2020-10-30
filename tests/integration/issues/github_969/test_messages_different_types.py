import numpy as np

from jina.flow import Flow
from jina.proto import jina_pb2
from jina.proto.ndarray.generic import GenericNdArray

random_np_array = np.random.randint(10, size=(50, 10))
buffer = 'text_buffer'.encode()
text = 'text_content'


def test_message_docs_different_chunk_types():
    def input_doc():
        doc = jina_pb2.Document()
        doc.tags['id'] = 1
        chunk0 = doc.chunks.add()
        chunk0.tags['id'] = 10
        chunk0.text = text
        GenericNdArray(chunk0.embedding).value = random_np_array
        chunk1 = doc.chunks.add()
        chunk1.tags['id'] = 20
        GenericNdArray(chunk1.blob).value = random_np_array
        chunk2 = doc.chunks.add()
        chunk2.tags['id'] = 30
        chunk2.buffer = buffer
        return doc

    def validate_fn(resp):
        assert len(resp.search.docs) == 1
        doc = resp.search.docs[0]
        assert int(doc.tags['id']) == 1
        assert len(doc.chunks) == 3

        chunk0 = doc.chunks[0]
        assert int(chunk0.tags['id']) == 10
        assert chunk0.text == text
        np.testing.assert_almost_equal(random_np_array, GenericNdArray(chunk0.embedding).value)

        chunk1 = doc.chunks[1]
        assert int(chunk1.tags['id']) == 20
        np.testing.assert_almost_equal(random_np_array, GenericNdArray(chunk1.blob).value)

        chunk2 = doc.chunks[2]
        assert int(chunk2.tags['id']) == 30
        assert chunk2.buffer == buffer

    with Flow().add(uses='_pass') as f:
        f.search(input_fn=[input_doc()], output_fn=validate_fn)


def test_message_docs_different_chunk_types_without_optimization():
    def input_doc():
        doc = jina_pb2.Document()
        doc.tags['id'] = 1
        chunk0 = doc.chunks.add()
        chunk0.tags['id'] = 10
        chunk0.text = text
        GenericNdArray(chunk0.embedding).value = random_np_array
        chunk1 = doc.chunks.add()
        chunk1.tags['id'] = 20
        GenericNdArray(chunk1.blob).value = random_np_array
        chunk2 = doc.chunks.add()
        chunk2.tags['id'] = 30
        chunk2.buffer = buffer
        return doc

    def validate_fn(resp):
        assert len(resp.search.docs) == 1
        doc = resp.search.docs[0]
        assert int(doc.tags['id']) == 1
        assert len(doc.chunks) == 3

        chunk0 = doc.chunks[0]
        assert int(chunk0.tags['id']) == 10
        assert chunk0.text == text
        np.testing.assert_almost_equal(random_np_array, GenericNdArray(chunk0.embedding).value)

        chunk1 = doc.chunks[1]
        assert int(chunk1.tags['id']) == 20
        np.testing.assert_almost_equal(random_np_array, GenericNdArray(chunk1.blob).value)

        chunk2 = doc.chunks[2]
        assert int(chunk2.tags['id']) == 30
        assert chunk2.buffer == buffer

    with Flow().add(uses='_pass') as f:
        f.search(input_fn=[input_doc()], output_fn=validate_fn)


def test_message_docs_different_matches_types():
    def input_doc():
        doc = jina_pb2.Document()
        doc.tags['id'] = 1
        match0 = doc.matches.add()
        match0.tags['id'] = 10
        match0.text = text
        GenericNdArray(match0.embedding).value = random_np_array
        match1 = doc.matches.add()
        match1.tags['id'] = 20
        GenericNdArray(match1.blob).value = random_np_array
        match2 = doc.matches.add()
        match2.tags['id'] = 30
        match2.buffer = buffer
        return doc

    def validate_fn(resp):
        assert len(resp.search.docs) == 1
        doc = resp.search.docs[0]
        assert int(doc.tags['id']) == 1
        assert len(doc.matches) == 3

        match0 = doc.matches[0]
        assert int(match0.tags['id']) == 10
        assert match0.text == text
        np.testing.assert_almost_equal(random_np_array, GenericNdArray(match0.embedding).value)

        match1 = doc.matches[1]
        assert int(match1.tags['id']) == 20
        np.testing.assert_almost_equal(random_np_array, GenericNdArray(match1.blob).value)

        match2 = doc.matches[2]
        assert int(match2.tags['id']) == 30
        assert match2.buffer == buffer

    with Flow().add(uses='_pass') as f:
        f.search(input_fn=[input_doc()], output_fn=validate_fn)


def test_message_docs_different_matches_types_without_optimization():
    def input_doc():
        doc = jina_pb2.Document()
        doc.tags['id'] = 1
        match0 = doc.matches.add()
        match0.tags['id'] = 10
        match0.text = text
        GenericNdArray(match0.embedding).value = random_np_array
        match1 = doc.matches.add()
        match1.tags['id'] = 20
        GenericNdArray(match1.blob).value = random_np_array
        match2 = doc.matches.add()
        match2.tags['id'] = 30
        match2.buffer = buffer
        return doc

    def validate_fn(resp):
        assert len(resp.search.docs) == 1
        doc = resp.search.docs[0]
        assert int(doc.tags['id']) == 1
        assert len(doc.matches) == 3

        match0 = doc.matches[0]
        assert int(match0.tags['id']) == 10
        assert match0.text == text
        np.testing.assert_almost_equal(random_np_array, GenericNdArray(match0.embedding).value)

        match1 = doc.matches[1]
        assert int(match1.tags['id']) == 20
        np.testing.assert_almost_equal(random_np_array, GenericNdArray(match1.blob).value)

        match2 = doc.matches[2]
        assert int(match2.tags['id']) == 30
        assert match2.buffer == buffer

    with Flow().add(uses='_pass') as f:
        f.search(input_fn=[input_doc()], output_fn=validate_fn)


def test_message_docs_different_chunks_and_matches_types():
    def input_doc():
        doc = jina_pb2.Document()
        doc.tags['id'] = 1
        chunk0 = doc.chunks.add()
        chunk0.tags['id'] = 10
        chunk0.text = text
        GenericNdArray(chunk0.embedding).value = random_np_array
        chunk1 = doc.chunks.add()
        chunk1.tags['id'] = 20
        GenericNdArray(chunk1.blob).value = random_np_array
        chunk2 = doc.chunks.add()
        chunk2.tags['id'] = 30
        chunk2.buffer = buffer
        match0 = doc.matches.add()
        match0.tags['id'] = 10
        match0.text = text
        GenericNdArray(match0.embedding).value = random_np_array
        match1 = doc.matches.add()
        match1.tags['id'] = 20
        GenericNdArray(match1.blob).value = random_np_array
        match2 = doc.matches.add()
        match2.tags['id'] = 30
        match2.buffer = buffer
        return doc

    def validate_fn(resp):
        assert len(resp.search.docs) == 1
        doc = resp.search.docs[0]
        assert int(doc.tags['id']) == 1
        assert len(doc.chunks) == 3

        chunk0 = doc.chunks[0]
        assert int(chunk0.tags['id']) == 10
        assert chunk0.text == text
        np.testing.assert_almost_equal(random_np_array, GenericNdArray(chunk0.embedding).value)

        chunk1 = doc.chunks[1]
        assert int(chunk1.tags['id']) == 20
        np.testing.assert_almost_equal(random_np_array, GenericNdArray(chunk1.blob).value)

        chunk2 = doc.chunks[2]
        assert int(chunk2.tags['id']) == 30
        assert chunk2.buffer == buffer

        assert len(doc.matches) == 3

        match0 = doc.matches[0]
        assert int(match0.tags['id']) == 10
        assert match0.text == text
        np.testing.assert_almost_equal(random_np_array, GenericNdArray(match0.embedding).value)

        match1 = doc.matches[1]
        assert int(match1.tags['id']) == 20
        np.testing.assert_almost_equal(random_np_array, GenericNdArray(match1.blob).value)

        match2 = doc.matches[2]
        assert int(match2.tags['id']) == 30
        assert match2.buffer == buffer

    with Flow().add(uses='_pass') as f:
        f.search(input_fn=[input_doc()], output_fn=validate_fn)


def test_message_docs_different_chunks_and_matches_types_without_optimization():
    def input_doc():
        doc = jina_pb2.Document()
        doc.tags['id'] = 1
        chunk0 = doc.chunks.add()
        chunk0.tags['id'] = 10
        chunk0.text = text
        GenericNdArray(chunk0.embedding).value = random_np_array
        chunk1 = doc.chunks.add()
        chunk1.tags['id'] = 20
        GenericNdArray(chunk1.blob).value = random_np_array
        chunk2 = doc.chunks.add()
        chunk2.tags['id'] = 30
        chunk2.buffer = buffer
        match0 = doc.matches.add()
        match0.tags['id'] = 10
        match0.text = text
        GenericNdArray(match0.embedding).value = random_np_array
        match1 = doc.matches.add()
        match1.tags['id'] = 20
        GenericNdArray(match1.blob).value = random_np_array
        match2 = doc.matches.add()
        match2.tags['id'] = 30
        match2.buffer = buffer
        return doc

    def validate_fn(resp):
        assert len(resp.search.docs) == 1
        doc = resp.search.docs[0]
        assert int(doc.tags['id']) == 1
        assert len(doc.chunks) == 3

        chunk0 = doc.chunks[0]
        assert int(chunk0.tags['id']) == 10
        assert chunk0.text == text
        np.testing.assert_almost_equal(random_np_array, GenericNdArray(chunk0.embedding).value)

        chunk1 = doc.chunks[1]
        assert int(chunk1.tags['id']) == 20
        np.testing.assert_almost_equal(random_np_array, GenericNdArray(chunk1.blob).value)

        chunk2 = doc.chunks[2]
        assert int(chunk2.tags['id']) == 30
        assert chunk2.buffer == buffer

        assert len(doc.matches) == 3

        match0 = doc.matches[0]
        assert int(match0.tags['id']) == 10
        assert match0.text == text
        np.testing.assert_almost_equal(random_np_array, GenericNdArray(match0.embedding).value)

        match1 = doc.matches[1]
        assert int(match1.tags['id']) == 20
        np.testing.assert_almost_equal(random_np_array, GenericNdArray(match1.blob).value)

        match2 = doc.matches[2]
        assert int(match2.tags['id']) == 30
        assert match2.buffer == buffer

    with Flow().add(uses='_pass') as f:
        f.search(input_fn=[input_doc()], output_fn=validate_fn)

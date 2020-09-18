from jina.flow import Flow
import numpy as np
from jina.proto import jina_pb2
from jina.drivers.helper import array2pb, pb2array

random_np_array = np.random.rand(50, 10)
buffer = 'text'.encode()


def test_message_docs_different_chunk_types():
    def input_doc():
        doc = jina_pb2.Document()
        doc.id = 1
        chunk0 = doc.chunks.add()
        chunk0.id = 10
        chunk0.text = 'text'
        chunk1 = doc.chunks.add()
        chunk1.id = 20
        chunk1.blob.CopyFrom(array2pb(random_np_array))
        chunk2 = doc.chunks.add()
        chunk2.id = 30
        chunk2.buffer = buffer
        return doc

    def validate_fn(resp):
        assert len(resp.search.docs) == 1
        doc = resp.search.docs[0]
        assert doc.id == 1
        assert len(doc.chunks) == 2

        chunk0 = doc.chunks[0]
        assert chunk0.id == 10
        assert chunk0.text == 'text'

        chunk1 = doc.chunks[1]
        assert chunk1.id == 20
        np.testing.assert_almost_equal(random_np_array, pb2array(chunk1.blob))

        chunk2 = doc.chunks[2]
        assert chunk2.id == 30
        assert chunk2.buffer == buffer

    with Flow().add(uses='_pass') as f:
        f.search(input_fn=[input_doc()], output_fn=validate_fn)


def test_message_docs_different_matches_types():
    def input_doc():
        doc = jina_pb2.Document()
        match0 = doc.matches.add()
        match0.id = 10
        match0.text = 'text'
        match1 = doc.matches.add()
        match1.id = 20
        match1.blob.CopyFrom(array2pb(random_np_array))
        match2 = doc.matches.add()
        match2.id = 30
        match2.buffer = buffer
        return doc

    def validate_fn(resp):
        assert len(resp.search.docs) == 1
        doc = resp.search.docs[0]
        assert doc.id == 1
        assert len(doc.matches) == 2

        match0 = doc.matches[0]
        assert match0.id == 10
        assert match0.text == 'text'

        match1 = doc.matches[1]
        assert match1.id == 20
        np.testing.assert_almost_equal(random_np_array, pb2array(match1.blob))

        match2 = doc.matches[2]
        assert match2.id == 30
        assert match2.buffer == buffer

    with Flow().add(uses='_pass') as f:
        f.search(input_fn=[input_doc()], output_fn=validate_fn)


def test_message_docs_different_chunks_and_matches_types():
    def input_doc():
        doc = jina_pb2.Document()
        chunk0 = doc.chunks.add()
        chunk0.id = 10
        chunk0.text = 'text'
        chunk1 = doc.chunks.add()
        chunk1.id = 20
        chunk1.blob.CopyFrom(array2pb(random_np_array))
        chunk2 = doc.chunks.add()
        chunk2.id = 30
        chunk2.buffer = buffer
        match0 = doc.matches.add()
        match0.id = 10
        match0.text = 'text'
        match1 = doc.matches.add()
        match1.id = 20
        match1.blob.CopyFrom(array2pb(random_np_array))
        match2 = doc.matches.add()
        match2.id = 30
        match2.buffer = buffer
        return doc

    def validate_fn(resp):
        assert len(resp.search.docs) == 1
        doc = resp.search.docs[0]
        assert doc.id == 1
        assert len(doc.chunks) == 2

        chunk0 = doc.chunks[0]
        assert chunk0.id == 10
        assert chunk0.text == 'text'

        chunk1 = doc.chunks[1]
        assert chunk1.id == 20
        np.testing.assert_almost_equal(random_np_array, pb2array(chunk1.blob))

        chunk2 = doc.chunks[2]
        assert chunk2.id == 30
        assert chunk2.buffer == buffer

        assert len(doc.matches) == 2

        match0 = doc.matches[0]
        assert match0.id == 10
        assert match0.text == 'text'

        match1 = doc.matches[1]
        assert match1.id == 20
        np.testing.assert_almost_equal(random_np_array, pb2array(match1.blob))

        match2 = doc.matches[2]
        assert match2.id == 30
        assert match2.buffer == buffer

    with Flow().add(uses='_pass') as f:
        f.search(input_fn=[input_doc()], output_fn=validate_fn)

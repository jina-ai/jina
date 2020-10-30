import numpy as np
from jina.peapods.zmq import _extract_bytes_from_documents
from jina.proto import jina_pb2
from jina.proto.ndarray.generic import GenericNdArray


def test_extract_bytes_from_msg_no_chunks():
    random_np_array = np.random.randint(10, size=(50, 10))
    buffer = 'text_buffer'.encode()
    text = 'text_content'

    def docs():
        doc0 = jina_pb2.Document()
        doc0.text = text
        GenericNdArray(doc0.embedding).value=random_np_array
        chunk = doc0.chunks.add()
        chunk.text = text
        doc1 = jina_pb2.Document()
        GenericNdArray(doc1.blob).value=random_np_array
        GenericNdArray(doc1.embedding).value=random_np_array
        doc2 = jina_pb2.Document()
        doc2.buffer = buffer
        GenericNdArray(doc2.embedding).value=random_np_array
        chunk2 = doc2.chunks.add()
        chunk2.text = text
        chunk3 = doc2.chunks.add()
        chunk3.buffer = buffer
        return [doc0, doc1, doc2]

    documents = docs()
    doc_bytes, chunk_bytes, chunk_byte_type = _extract_bytes_from_documents(documents)
    assert len(doc_bytes) == 3
    assert len(chunk_bytes) == 6
    assert chunk_bytes[0] == b''
    assert chunk_bytes[1] == text.encode()
    assert chunk_bytes[2] == b''
    assert chunk_bytes[3] == text.encode()
    assert chunk_bytes[4] == b''
    assert chunk_bytes[5] == buffer
    assert chunk_byte_type == b'buffer'

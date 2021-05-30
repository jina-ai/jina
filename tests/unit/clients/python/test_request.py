import os
import sys

import numpy as np
import pytest
from google.protobuf.json_format import MessageToJson, MessageToDict

from jina import Document, Flow
from jina.clients.request import request_generator
from jina.clients.request.helper import _new_doc_from_data
from jina.enums import DataInputType
from jina.excepts import BadDocType
from jina.proto import jina_pb2
from jina.proto.jina_pb2 import DocumentProto
from jina.types.ndarray.generic import NdArray


@pytest.mark.skipif(
    sys.version_info < (3, 8, 0),
    reason='somehow this does not work on Github workflow with Py3.7, '
    'but Py 3.8 is fine, local Py3.7 is fine',
)
def test_on_bad_iterator():
    # this should not stuck the server as request_generator's error is handled on the client side
    f = Flow().add()
    with f:
        f.index([1, 2, 3])


@pytest.mark.parametrize(
    'builder',
    [
        lambda x: x.SerializeToString(),
        lambda x: MessageToJson(x),
        lambda x: MessageToDict(x),
        lambda x: Document(x),
    ],
)
def test_data_type_builder_doc(builder):
    a = DocumentProto()
    a.id = 'a236cbb0eda62d58'
    d, t = _new_doc_from_data(builder(a), DataInputType.DOCUMENT)
    assert d.id == a.id
    assert t == DataInputType.DOCUMENT


def test_data_type_builder_doc_bad():
    a = DocumentProto()
    a.id = 'a236cbb0eda62d58'
    with pytest.raises(BadDocType):
        _new_doc_from_data(b'BREAKIT!' + a.SerializeToString(), DataInputType.DOCUMENT)

    with pytest.raises(BadDocType):
        _new_doc_from_data(MessageToJson(a) + '🍔', DataInputType.DOCUMENT)


@pytest.mark.parametrize('input_type', [DataInputType.AUTO, DataInputType.CONTENT])
def test_data_type_builder_auto(input_type):
    if 'JINA_ARRAY_QUANT' in os.environ:
        print(f'quant is on: {os.environ["JINA_ARRAY_QUANT"]}')
        del os.environ['JINA_ARRAY_QUANT']

    d, t = _new_doc_from_data('123', input_type)
    assert d.text == '123'
    assert t == DataInputType.CONTENT

    d, t = _new_doc_from_data(b'45678', input_type)
    assert t == DataInputType.CONTENT
    assert d.buffer == b'45678'

    d, t = _new_doc_from_data(b'123', input_type)
    assert t == DataInputType.CONTENT
    assert d.buffer == b'123'

    c = np.random.random([10, 10])
    d, t = _new_doc_from_data(c, input_type)
    np.testing.assert_equal(d.blob, c)
    assert t == DataInputType.CONTENT


def test_request_generate_lines():
    def random_lines(num_lines):
        for j in range(1, num_lines + 1):
            yield f'i\'m dummy doc {j}'

    req = request_generator('', data=random_lines(100), request_size=100)

    request = next(req)
    assert len(request.docs) == 100
    assert request.docs[0].mime_type == 'text/plain'
    assert request.docs[0].text == 'i\'m dummy doc 1'


def test_request_generate_lines_from_list():
    def random_lines(num_lines):
        return [f'i\'m dummy doc {j}' for j in range(1, num_lines + 1)]

    req = request_generator('', data=random_lines(100), request_size=100)

    request = next(req)
    assert len(request.docs) == 100
    for index, doc in enumerate(request.docs, 1):
        assert doc.mime_type == 'text/plain'
        assert doc.text == f'i\'m dummy doc {index}'


def test_request_generate_bytes():
    def random_lines(num_lines):
        for j in range(1, num_lines + 1):
            yield f'i\'m dummy doc {j}'

    req = request_generator('', data=random_lines(100), request_size=100)

    request = next(req)
    assert len(request.docs) == 100
    for index, doc in enumerate(request.docs, 1):
        assert doc.text == f'i\'m dummy doc {index}'
        assert doc.mime_type == 'text/plain'


def test_request_generate_docs():
    def random_docs(num_docs):
        for j in range(1, num_docs + 1):
            doc = jina_pb2.DocumentProto()
            doc.text = f'i\'m dummy doc {j}'
            doc.offset = 1000
            doc.tags['id'] = 1000  # this will be ignored
            doc.mime_type = 'mime_type'
            yield doc

    req = request_generator('', data=random_docs(100), request_size=100)

    request = next(req)
    assert len(request.docs) == 100
    for index, doc in enumerate(request.docs, 1):
        assert doc.mime_type == 'mime_type'
        assert doc.text == f'i\'m dummy doc {index}'
        assert doc.offset == 1000


def test_request_generate_dict():
    def random_docs(num_docs):
        for j in range(1, num_docs + 1):
            doc = {
                'text': f'i\'m dummy doc {j}',
                'offset': 1000,
                'tags': {'id': 1000},
                'chunks': [
                    {'text': f'i\'m chunk 1', 'modality': 'text'},
                    {'text': f'i\'m chunk 2', 'modality': 'image'},
                ],
            }
            yield doc

    req = request_generator('', data=random_docs(100), request_size=100)

    request = next(req)
    assert len(request.docs) == 100
    for index, doc in enumerate(request.docs, 1):
        assert doc.text == f'i\'m dummy doc {index}'
        assert doc.offset == 1000
        assert doc.tags['id'] == 1000
        assert len(doc.chunks) == 2
        assert doc.chunks[0].modality == 'text'
        assert doc.chunks[0].text == f'i\'m chunk 1'
        assert doc.chunks[1].modality == 'image'
        assert doc.chunks[1].text == f'i\'m chunk 2'


def test_request_generate_dict_str():
    import json

    def random_docs(num_docs):
        for j in range(1, num_docs + 1):
            doc = {
                'text': f'i\'m dummy doc {j}',
                'offset': 1000,
                'tags': {'id': 1000},
                'chunks': [
                    {'text': f'i\'m chunk 1', 'modality': 'text'},
                    {'text': f'i\'m chunk 2', 'modality': 'image'},
                ],
            }
            yield json.dumps(doc)

    req = request_generator('', data=random_docs(100), request_size=100)

    request = next(req)
    assert len(request.docs) == 100
    for index, doc in enumerate(request.docs, 1):
        assert doc.text == f'i\'m dummy doc {index}'
        assert doc.offset == 1000
        assert doc.tags['id'] == 1000
        assert len(doc.chunks) == 2
        assert doc.chunks[0].modality == 'text'
        assert doc.chunks[0].text == f'i\'m chunk 1'
        assert doc.chunks[1].modality == 'image'
        assert doc.chunks[1].text == f'i\'m chunk 2'


def test_request_generate_numpy_arrays():
    input_array = np.random.random([10, 10])

    req = request_generator('', data=input_array, request_size=5)

    request = next(req)
    assert len(request.docs) == 5
    for index, doc in enumerate(request.docs, 1):
        assert NdArray(doc.blob).value.shape == (10,)

    request = next(req)
    assert len(request.docs) == 5
    for index, doc in enumerate(request.docs, 1):
        assert NdArray(doc.blob).value.shape == (10,)


def test_request_generate_numpy_arrays_iterator():
    input_array = np.random.random([10, 10])

    def generator():
        for array in input_array:
            yield array

    req = request_generator('', data=generator(), request_size=5)

    request = next(req)
    assert len(request.docs) == 5
    for index, doc in enumerate(request.docs, 1):
        assert NdArray(doc.blob).value.shape == (10,)

    request = next(req)
    assert len(request.docs) == 5
    for index, doc in enumerate(request.docs, 1):
        assert NdArray(doc.blob).value.shape == (10,)

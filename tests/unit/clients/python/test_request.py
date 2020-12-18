import os

import numpy as np
import pytest
from google.protobuf.json_format import MessageToJson, MessageToDict

from jina import Document, Flow
from jina.clients.request import _generate, _build_doc
from jina.enums import DataInputType
from jina.excepts import BadDocType
from jina.proto import jina_pb2
from jina.proto.jina_pb2 import DocumentProto
from jina.types.ndarray.generic import NdArray

import sys

@pytest.mark.skipif(sys.version_info < (3, 8, 0), reason='somehow this does not work on Github workflow with Py3.7, '
                                                         'but Py 3.8 is fine, local Py3.7 is fine')
def test_on_bad_iterator():
    # this should not stuck the server as request_generator's error is handled on the client side
    f = Flow().add()
    with f:
        f.index([1, 2, 3])


@pytest.mark.parametrize('builder', [lambda x: x.SerializeToString(),
                                     lambda x: MessageToJson(x),
                                     lambda x: MessageToDict(x),
                                     lambda x: Document(x)])
def test_data_type_builder_doc(builder):
    a = DocumentProto()
    a.id = 'a236cbb0eda62d58'
    d, t = _build_doc(builder(a), DataInputType.DOCUMENT)
    assert d.id == a.id
    assert t == DataInputType.DOCUMENT


def test_data_type_builder_doc_bad():
    a = DocumentProto()
    a.id = 'a236cbb0eda62d58'
    with pytest.raises(BadDocType):
        _build_doc(b'BREAKIT!' + a.SerializeToString(), DataInputType.DOCUMENT)

    with pytest.raises(BadDocType):
        _build_doc(MessageToJson(a) + '🍔', DataInputType.DOCUMENT)

    with pytest.raises(BadDocType):
        _build_doc({'🍔': '🍔'}, DataInputType.DOCUMENT)


@pytest.mark.parametrize('input_type', [DataInputType.AUTO, DataInputType.CONTENT])
def test_data_type_builder_auto(input_type):
    if 'JINA_ARRAY_QUANT' in os.environ:
        print(f'quant is on: {os.environ["JINA_ARRAY_QUANT"]}')
        del os.environ['JINA_ARRAY_QUANT']

    d, t = _build_doc('123', input_type)
    assert d.text == '123'
    assert t == DataInputType.CONTENT

    d, t = _build_doc(b'45678', input_type)
    assert t == DataInputType.CONTENT
    assert d.buffer == b'45678'

    d, t = _build_doc(b'123', input_type)
    assert t == DataInputType.CONTENT
    assert d.buffer == b'123'

    c = np.random.random([10, 10])
    d, t = _build_doc(c, input_type)
    np.testing.assert_equal(d.blob, c)
    assert t == DataInputType.CONTENT


def test_request_generate_lines():
    def random_lines(num_lines):
        for j in range(1, num_lines + 1):
            yield f'i\'m dummy doc {j}'

    req = _generate(data=random_lines(100), batch_size=100)

    request = next(req)
    assert len(request.index.docs) == 100
    for index, doc in enumerate(request.index.docs, 1):
        assert doc.length == 100
        assert doc.mime_type == 'text/plain'
        assert doc.text == f'i\'m dummy doc {index}'


def test_request_generate_lines_from_list():
    def random_lines(num_lines):
        return [f'i\'m dummy doc {j}' for j in range(1, num_lines + 1)]

    req = _generate(data=random_lines(100), batch_size=100)

    request = next(req)
    assert len(request.index.docs) == 100
    for index, doc in enumerate(request.index.docs, 1):
        assert doc.length == 100
        assert doc.mime_type == 'text/plain'
        assert doc.text == f'i\'m dummy doc {index}'


def test_request_generate_lines_with_fake_url():
    def random_lines(num_lines):
        for j in range(1, num_lines + 1):
            yield f'https://github.com i\'m dummy doc {j}'

    req = _generate(data=random_lines(100), batch_size=100)

    request = next(req)
    assert len(request.index.docs) == 100
    for index, doc in enumerate(request.index.docs, 1):
        assert doc.length == 100
        assert doc.mime_type == 'text/plain'
        assert doc.text == f'https://github.com i\'m dummy doc {index}'


def test_request_generate_bytes():
    def random_lines(num_lines):
        for j in range(1, num_lines + 1):
            yield f'i\'m dummy doc {j}'

    req = _generate(data=random_lines(100), batch_size=100)

    request = next(req)
    assert len(request.index.docs) == 100
    for index, doc in enumerate(request.index.docs, 1):
        assert doc.length == 100
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

    req = _generate(data=random_docs(100), batch_size=100)

    request = next(req)
    assert len(request.index.docs) == 100
    for index, doc in enumerate(request.index.docs, 1):
        assert doc.length == 100
        assert doc.mime_type == 'mime_type'
        assert doc.text == f'i\'m dummy doc {index}'
        assert doc.offset == 1000


def test_request_generate_dict():
    def random_docs(num_docs):
        for j in range(1, num_docs + 1):
            doc = {
                'text': f'i\'m dummy doc {j}',
                'offset': 1000,
                'tags': {
                    'id': 1000
                },
                'chunks': [
                    {
                        'text': f'i\'m chunk 1',
                        'modality': 'text'
                    },
                    {
                        'text': f'i\'m chunk 2',
                        'modality': 'image'
                    },
                ]
            }
            yield doc

    req = _generate(data=random_docs(100), batch_size=100)

    request = next(req)
    assert len(request.index.docs) == 100
    for index, doc in enumerate(request.index.docs, 1):
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
                'tags': {
                    'id': 1000
                },
                'chunks': [
                    {
                        'text': f'i\'m chunk 1',
                        'modality': 'text'
                    },
                    {
                        'text': f'i\'m chunk 2',
                        'modality': 'image'
                    },
                ]
            }
            yield json.dumps(doc)

    req = _generate(data=random_docs(100), batch_size=100)

    request = next(req)
    assert len(request.index.docs) == 100
    for index, doc in enumerate(request.index.docs, 1):
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

    req = _generate(data=input_array, batch_size=5)

    request = next(req)
    assert len(request.index.docs) == 5
    for index, doc in enumerate(request.index.docs, 1):
        assert doc.length == 5
        assert NdArray(doc.blob).value.shape == (10,)

    request = next(req)
    assert len(request.index.docs) == 5
    for index, doc in enumerate(request.index.docs, 1):
        assert doc.length == 5
        assert NdArray(doc.blob).value.shape == (10,)


def test_request_generate_numpy_arrays_iterator():
    input_array = np.random.random([10, 10])

    def generator():
        for array in input_array:
            yield array

    req = _generate(data=generator(), batch_size=5)

    request = next(req)
    assert len(request.index.docs) == 5
    for index, doc in enumerate(request.index.docs, 1):
        assert doc.length == 5
        assert NdArray(doc.blob).value.shape == (10,)

    request = next(req)
    assert len(request.index.docs) == 5
    for index, doc in enumerate(request.index.docs, 1):
        assert doc.length == 5
        assert NdArray(doc.blob).value.shape == (10,)

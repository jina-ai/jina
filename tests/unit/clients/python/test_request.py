import os

import numpy as np
import pytest
from docarray import Document

from jina.clients.request import request_generator
from jina.clients.request.helper import _new_doc_from_data
from jina.enums import DataInputType


@pytest.mark.parametrize(
    'builder, input_data_type, output_data_type',
    [
        (lambda x: x.to_dict(), DataInputType.AUTO, DataInputType.DICT),
        (lambda x: x, DataInputType.DOCUMENT, DataInputType.DOCUMENT),
        (lambda x: x, DataInputType.AUTO, DataInputType.DOCUMENT),
        (lambda x: x.text, DataInputType.CONTENT, DataInputType.CONTENT),
    ],
)
def test_data_type_builder_doc(builder, input_data_type, output_data_type):
    a = Document()
    a.id = 'a236cbb0eda62d58'
    a.text = 'text test'
    d, t = _new_doc_from_data(builder(a), input_data_type)
    if input_data_type != DataInputType.CONTENT:
        assert d.id == a.id
    assert d.text == a.text
    assert t == output_data_type


@pytest.mark.parametrize('request_schema', [DataInputType.AUTO, DataInputType.CONTENT])
def test_data_type_builder_auto(request_schema):
    if 'JINA_ARRAY_QUANT' in os.environ:
        print(f'quant is on: {os.environ["JINA_ARRAY_QUANT"]}')
        del os.environ['JINA_ARRAY_QUANT']

    d, t = _new_doc_from_data('123', request_schema)
    assert d.text == '123'
    assert t == DataInputType.CONTENT

    d, t = _new_doc_from_data(b'123', request_schema)
    assert t == DataInputType.CONTENT
    assert d.blob == b'123'

    c = np.random.random([10, 10])
    d, t = _new_doc_from_data(c, request_schema)
    np.testing.assert_equal(d.tensor, c)
    assert t == DataInputType.CONTENT


def test_request_generate_lines():
    def random_lines(num_lines):
        for j in range(1, num_lines + 1):
            yield f'i\'m dummy doc {j}'

    req = request_generator('', data=random_lines(100), request_size=100)

    request = next(req)
    assert len(request.docs) == 100
    assert request.docs[0].text == 'i\'m dummy doc 1'


def test_request_generate_lines_from_list():
    def random_lines(num_lines):
        return [f'i\'m dummy doc {j}' for j in range(1, num_lines + 1)]

    req = request_generator('', data=random_lines(100), request_size=100)

    request = next(req)
    assert len(request.docs) == 100
    for index, doc in enumerate(request.docs, 1):
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


def test_request_generate_docs():
    def random_docs(num_docs):
        for j in range(1, num_docs + 1):
            doc = Document()
            doc.text = f'i\'m dummy doc {j}'
            doc.offset = 1000
            doc.tags['id'] = 1000  # this will be ignored
            yield doc

    req = request_generator('', data=random_docs(100), request_size=100)

    request = next(req)
    assert len(request.docs) == 100
    for index, doc in enumerate(request.docs, 1):
        assert doc.text == f'i\'m dummy doc {index}'
        assert doc.offset == 1000


def test_request_generate_dict():
    def random_docs(num_docs):
        for j in range(1, num_docs + 1):
            doc = {
                'id': f'root {j}',
                'text': f'i\'m dummy doc {j}',
                'offset': 1000,
                'tags': {'id': 1000},
                'chunks': [
                    {'id': 'c1', 'text': f'i\'m chunk 1', 'modality': 'text'},
                    {'id': 'c2', 'text': f'i\'m chunk 2', 'modality': 'image'},
                ],
            }
            yield doc

    req = request_generator('', data=random_docs(100), request_size=100)

    request = next(req)
    assert len(request.docs) == 100
    for index, doc in enumerate(request.docs, 1):
        assert doc.text == f'i\'m dummy doc {index}'
        assert doc.id == f'root {index}'
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
                'id': f'root {j}',
                'text': f'i\'m dummy doc {j}',
                'offset': 1000,
                'tags': {'id': 1000},
                'chunks': [
                    {'id': 'c1', 'text': f'i\'m chunk 1', 'modality': 'text'},
                    {'id': 'c2', 'text': f'i\'m chunk 2', 'modality': 'image'},
                ],
            }
            yield doc

    req = request_generator('', data=random_docs(100), request_size=100)

    request = next(req)
    assert len(request.docs) == 100
    for index, doc in enumerate(request.docs, 1):
        assert doc.id == f'root {index}'
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
        assert doc.tensor.shape == (10,)

    request = next(req)
    assert len(request.docs) == 5
    for index, doc in enumerate(request.docs, 1):
        assert doc.tensor.shape == (10,)


def test_request_generate_numpy_arrays_iterator():
    input_array = np.random.random([10, 10])

    def generator():
        for array in input_array:
            yield array

    req = request_generator('', data=generator(), request_size=5)

    request = next(req)
    assert len(request.docs) == 5
    for index, doc in enumerate(request.docs, 1):
        assert doc.tensor.shape == (10,)

    request = next(req)
    assert len(request.docs) == 5
    for index, doc in enumerate(request.docs, 1):
        assert doc.tensor.shape == (10,)

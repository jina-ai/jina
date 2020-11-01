import numpy as np

from jina.clients.python.request import _generate
from jina.proto import jina_pb2
from jina.proto.ndarray.generic import GenericNdArray


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
            doc = jina_pb2.Document()
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


def test_request_generate_numpy_arrays():
    input_array = np.random.random([10, 10])

    req = _generate(data=input_array, batch_size=5)

    request = next(req)
    assert len(request.index.docs) == 5
    for index, doc in enumerate(request.index.docs, 1):
        assert doc.length == 5
        assert GenericNdArray(doc.blob).value.shape == (10,)

    request = next(req)
    assert len(request.index.docs) == 5
    for index, doc in enumerate(request.index.docs, 1):
        assert doc.length == 5
        assert GenericNdArray(doc.blob).value.shape == (10,)


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
        assert GenericNdArray(doc.blob).value.shape == (10,)

    request = next(req)
    assert len(request.index.docs) == 5
    for index, doc in enumerate(request.index.docs, 1):
        assert doc.length == 5
        assert GenericNdArray(doc.blob).value.shape == (10,)

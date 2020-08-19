from jina.clients.python.request import _generate
from jina.proto import jina_pb2
from jina.drivers.helper import pb2array
from tests import JinaTestCase

import numpy as np


class RequestTestCase(JinaTestCase):

    def test_request_generate_lines(self):
        def random_lines(num_lines):
            for j in range(1, num_lines + 1):
                yield f'i\'m dummy doc {j}'

        req = _generate(data=random_lines(100), batch_size=100)

        request = next(req)
        self.assertEqual(len(request.index.docs), 100)
        for index, doc in enumerate(request.index.docs, 1):
            self.assertEqual(doc.id, index)
            self.assertEqual(doc.length, 100)
            self.assertEqual(doc.mime_type, 'text/plain')
            self.assertEqual(doc.level_depth, 0)
            self.assertEqual(doc.text, f'i\'m dummy doc {index}')

    def test_request_generate_lines_from_list(self):
        def random_lines(num_lines):
            return [f'i\'m dummy doc {j}' for j in range(1, num_lines + 1)]

        req = _generate(data=random_lines(100), batch_size=100)

        request = next(req)
        self.assertEqual(len(request.index.docs), 100)
        for index, doc in enumerate(request.index.docs, 1):
            self.assertEqual(doc.id, index)
            self.assertEqual(doc.length, 100)
            self.assertEqual(doc.mime_type, 'text/plain')
            self.assertEqual(doc.level_depth, 0)
            self.assertEqual(doc.text, f'i\'m dummy doc {index}')

    def test_request_generate_lines_with_fake_url(self):
        def random_lines(num_lines):
            for j in range(1, num_lines + 1):
                yield f'https://github.com i\'m dummy doc {j}'

        req = _generate(data=random_lines(100), batch_size=100)

        request = next(req)
        self.assertEqual(len(request.index.docs), 100)
        for index, doc in enumerate(request.index.docs, 1):
            self.assertEqual(doc.id, index)
            self.assertEqual(doc.length, 100)
            self.assertEqual(doc.mime_type, 'text/plain')
            self.assertEqual(doc.level_depth, 0)
            self.assertEqual(doc.text, f'https://github.com i\'m dummy doc {index}')

    def test_request_generate_docs(self):
        def random_docs(num_docs):
            for j in range(1, num_docs + 1):
                doc = jina_pb2.Document
                doc.text = f'i\'m dummy doc {j}'
                doc.offset = 1000
                doc.id = 1000  # this will be ignored
                doc.level_depth = 3  # this will not be ignored
                yield doc

        req = _generate(data=random_docs(100), batch_size=100)

        request = next(req)
        self.assertEqual(len(request.index.docs), 100)
        for index, doc in enumerate(request.index.docs, 1):
            self.assertEqual(doc.id, index)
            self.assertEqual(doc.length, 100)
            self.assertEqual(doc.mime_type, 'text/plain')
            self.assertEqual(doc.level_depth, 3)
            self.assertEqual(doc.text, f'i\'m dummy doc {index}')
            self.assertEqual(doc.offset, 1000)

    def test_request_generate_numpy_arrays(self):

        input_array = np.random.random([10, 10])

        req = _generate(data=input_array, batch_size=5)

        request = next(req)
        self.assertEqual(len(request.index.docs), 5)
        for index, doc in enumerate(request.index.docs, 1):
            self.assertEqual(doc.id, index)
            self.assertEqual(doc.length, 5)
            self.assertEqual(doc.level_depth, 0)
            np.testing.assert_almost_equal(pb2array(doc.blob), input_array[doc.id - 1])

        request = next(req)
        self.assertEqual(len(request.index.docs), 5)
        for index, doc in enumerate(request.index.docs, 1):
            self.assertEqual(doc.id, 5 + index)
            self.assertEqual(doc.length, 5)
            self.assertEqual(doc.level_depth, 0)
            np.testing.assert_almost_equal(pb2array(doc.blob), input_array[doc.id - 1])

    def test_request_generate_numpy_arrays_iterator(self):

        input_array = np.random.random([10, 10])

        def generator():
            for array in input_array:
                yield array

        req = _generate(data=generator(), batch_size=5)

        request = next(req)
        self.assertEqual(len(request.index.docs), 5)
        for index, doc in enumerate(request.index.docs, 1):
            self.assertEqual(doc.id, index)
            self.assertEqual(doc.length, 5)
            self.assertEqual(doc.level_depth, 0)
            np.testing.assert_almost_equal(pb2array(doc.blob), input_array[doc.id - 1])

        request = next(req)
        self.assertEqual(len(request.index.docs), 5)
        for index, doc in enumerate(request.index.docs, 1):
            self.assertEqual(doc.id, 5 + index)
            self.assertEqual(doc.length, 5)
            self.assertEqual(doc.level_depth, 0)
            np.testing.assert_almost_equal(pb2array(doc.blob), input_array[doc.id - 1])

    def test_request_generate_docs_with_different_level_depth(self):
        def random_docs(num_docs):
            for j in range(1, num_docs + 1):
                doc = jina_pb2.Document
                doc.text = f'i\'m dummy doc {j}'
                doc.offset = 1000
                doc.id = 1000  # this will be ignored
                doc.level_depth = 3  # this will be overriden by _generate level_depth param
                yield doc

        req = _generate(data=random_docs(100), batch_size=100, level_depth=5)

        request = next(req)
        self.assertEqual(len(request.index.docs), 100)
        for index, doc in enumerate(request.index.docs, 1):
            self.assertEqual(doc.id, index)
            self.assertEqual(doc.length, 100)
            self.assertEqual(doc.mime_type, 'text/plain')
            self.assertEqual(doc.level_depth, 5)
            self.assertEqual(doc.text, f'i\'m dummy doc {index}')
            self.assertEqual(doc.offset, 1000)

import unittest

from jina.executors.crafters import BaseSegmenter
from jina.flow import Flow
from jina.proto import jina_pb2
from tests import JinaTestCase


def random_docs(num_docs):
    for j in range(num_docs):
        d = jina_pb2.Document()
        d.id = j
        d.text = 'hello world'
        yield d


class DummySegmenter(BaseSegmenter):

    def craft(self, text, *args, **kwargs):
        return [{'text': 'adasd' * j} for j in range(10)]


class MyTestCase(JinaTestCase):

    def test_sort_ql(self):
        pass

    def test_segment_driver(self):
        def validate(req):
            self.assertEqual(len(req.docs[0].chunks), 10)
            self.assertEqual(len(req.docs[-1].chunks), 10)

        f = Flow().add(uses='DummySegmenter')

        with f:
            f.index(random_docs(10), output_fn=validate, callback_on_body=True)


if __name__ == '__main__':
    unittest.main()

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
        d.uri = 'doc://'
        for m in range(10):
            dm = d.matches.add()
            dm.text = 'match to hello world'
            dm.uri = 'doc://match'
            dm.id = m
            dm.score.ref_id = d.id
            for mm in range(10):
                dmm = dm.matches.add()
                dmm.text = 'nested match to match'
                dmm.uri = 'doc://match/match'
                dmm.id = mm
                dmm.score.ref_id = m
        yield d


class DummySegmenter(BaseSegmenter):

    def craft(self, text, *args, **kwargs):
        return [{'text': 'adasd' * (j + 1)} for j in range(10)]


class QueryLangTestCase(JinaTestCase):

    def test_sort_ql(self):
        pass

    def test_segment_driver(self):
        def validate(req):
            self.assertNotEqual(req.docs[0].text, '')
            self.assertNotEqual(req.docs[-1].text, '')
            self.assertNotEqual(req.docs[0].chunks[0].text, '')
            self.assertNotEqual(req.docs[0].matches[0].text, '')
            self.assertNotEqual(req.docs[0].matches[0].matches[-1].text, '')
            self.assertEqual(len(req.docs[0].chunks), 10)
            self.assertEqual(len(req.docs[-1].chunks), 10)
            self.assertEqual(len(req.docs[0].matches), 10)
            self.assertEqual(len(req.docs[-1].matches), 10)
            self.assertEqual(len(req.docs[-1].matches[0].matches), 10)
            self.assertEqual(len(req.docs[-1].matches[-1].matches), 10)

        f = Flow().add(uses='DummySegmenter')

        with f:
            f.index(random_docs(10), output_fn=validate, callback_on_body=True)

    def test_slice_ql(self):
        def validate(req):
            self.assertEqual(len(req.docs), 2)  # slice on level 0
            self.assertEqual(len(req.docs[0].chunks), 2)  # slice on level 1
            self.assertEqual(len(req.docs[-1].chunks), 2)  # slice on level 1
            self.assertEqual(len(req.docs[0].matches), 2)  # slice on level 1 for matches
            self.assertEqual(len(req.docs[-1].matches[0].matches), 2)  # slice on level 2 for matches

        f = (Flow().add(uses='DummySegmenter')
             .add(uses='- !SliceQL | {start: 0, end: 2, traverse_on: ["chunks"], depth_range: [0, 2]}')
             .add(uses='- !SliceQL | {start: 0, end: 2, traverse_on: ["matches"], depth_range: [0, 2]}'))

        with f:
            f.index(random_docs(10), output_fn=validate, callback_on_body=True)

        f = (Flow().add(uses='DummySegmenter')
             .add(uses='- !SliceQL | {start: 0, end: 2, traverse_on: [chunks, matches], depth_range: [0, 2]}'))

        with f:
            f.index(random_docs(10), output_fn=validate, callback_on_body=True)

    def test_select_ql(self):
        def validate(req):
            self.assertEqual(req.docs[0].text, '')
            self.assertEqual(req.docs[-1].text, '')
            self.assertEqual(req.docs[0].matches[0].text, '')
            self.assertEqual(req.docs[0].chunks[0].text, '')

        f = (Flow().add(uses='DummySegmenter')
            .add(
            uses='- !SelectQL | {fields: [uri, matches, chunks], traverse_on: [chunks, matches], depth_range: [0, 2]}'))

        with f:
            f.index(random_docs(10), output_fn=validate, callback_on_body=True)

        f = (Flow().add(uses='DummySegmenter')
             .add(uses='- !ExcludeQL | {fields: [text], traverse_on: [chunks, matches], depth_range: [0, 2]}'))

        with f:
            f.index(random_docs(10), output_fn=validate, callback_on_body=True)


if __name__ == '__main__':
    unittest.main()

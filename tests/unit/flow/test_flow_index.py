import os
import time
import unittest

from jina.flow import Flow
from jina.proto import jina_pb2
from tests import JinaTestCase, random_docs

cur_dir = os.path.dirname(os.path.abspath(__file__))


def random_queries(num_docs, chunks_per_doc=5):
    for j in range(num_docs):
        d = jina_pb2.Document()
        for k in range(chunks_per_doc):
            dd = d.add()
            dd.id = k + 1  # 1-indexed
        yield d


class FlowTestCase(JinaTestCase):

    @unittest.skipIf('GITHUB_WORKFLOW' in os.environ, 'skip the network test on github workflow')
    def test_shards_insufficient_data(self):
        """THIS IS SUPER IMPORTANT FOR TESTING SHARDS

        IF THIS FAILED, DONT IGNORE IT, DEBUG IT
        """
        index_docs = 3
        parallel = 4

        def validate(req):
            assert len(req.docs) == 1
            assert len(req.docs[0].matches) == index_docs

            for d in req.docs[0].matches:
                self.assertTrue(hasattr(d, 'weight'))
                self.assertIsNotNone(d.weight)
                assert d.meta_info == b'hello world'

        f = Flow().add(name='doc_pb', uses=os.path.join(cur_dir, '../yaml/test-docpb.yml'), parallel=parallel,
                       separated_workspace=True)
        with f:
            f.index(input_fn=random_docs(index_docs), random_doc_id=False)

        time.sleep(2)
        with f:
            pass
        time.sleep(2)
        f = Flow().add(name='doc_pb', uses=os.path.join(cur_dir, '../yaml/test-docpb.yml'), parallel=parallel,
                       separated_workspace=True, polling='all', uses_reducing='_merge_all')
        with f:
            f.search(input_fn=random_queries(1, index_docs), random_doc_id=False, output_fn=validate,
                     callback_on_body=True)
        time.sleep(2)
        self.add_tmpfile('test-docshard-tmp')

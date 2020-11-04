import os
from typing import List, Dict

import numpy as np

from jina.executors.crafters import BaseSegmenter
from jina.executors.encoders import BaseEncoder
from jina.executors.indexers.keyvalue import BinaryPbIndexer
from jina.flow import Flow
from jina.proto import jina_pb2, uid

# import Document

cur_dir = os.path.dirname(os.path.abspath(__file__))


class MockSegmenter(BaseSegmenter):

    def craft(self, text: str, *args, **kwargs) -> List[Dict]:
        split = text.split(',')
        chunks = [dict(text=split[0], offset=0, weight=1.0, modality='mode1'),
                  dict(text=split[1], offset=1, weight=1.0, modality='mode2')]
        return chunks


class MockEncoder(BaseEncoder):

    def encode(self, data: str, *args, **kwargs) -> 'np.ndarray':
        output = []
        for r in data:
            if "mode1" in r:
                output.append([0.0, 0.0, 0.0])
            elif "mode2" in r:
                output.append([1.0, 1.0, 1.0])

        return np.array(output)


def test_flow_with_modalities(tmpdir):
    os.environ['JINA_TEST_FLOW_MULTIMODE_WORKSPACE'] = str(tmpdir)

    def input_fn():
        doc1 = jina_pb2.Document()
        doc1.text = 'title: this is mode1 from doc1, body: this is mode2 from doc1'
        doc1.id = uid.new_doc_id(doc1)

        doc2 = jina_pb2.Document()
        doc2.text = 'title: this is mode1 from doc2, body: this is mode2 from doc2'
        doc2.id = uid.new_doc_id(doc2)

        doc3 = jina_pb2.Document()
        doc3.text = 'title: this is mode1 from doc3, body: this is mode2 from doc3'
        doc3.id = uid.new_doc_id(doc3)

        return [doc1, doc2, doc3]

    flow = Flow().add(name='crafter', uses='!MockSegmenter'). \
        add(name='encoder1', uses=os.path.join(cur_dir, 'yaml/mockencoder-mode1.yml')). \
        add(name='indexer1', uses=os.path.join(cur_dir, 'yaml/numpy-indexer-1.yml'), needs=['encoder1']). \
        add(name='encoder2', uses=os.path.join(cur_dir, 'yaml/mockencoder-mode2.yml'), needs=['crafter']). \
        add(name='indexer2', uses=os.path.join(cur_dir, 'yaml/numpy-indexer-2.yml')). \
        join(['indexer1', 'indexer2'])

    with flow:
        flow.index(input_fn=input_fn, override_doc_id=False)

    with open(tmpdir.join('vec1.gz'), 'rb') as fp:
        result = np.frombuffer(fp.read(), dtype='float').reshape([-1, 3])
        np.testing.assert_equal(result, np.array([[0.0, 0.0, 0.0],
                                                  [0.0, 0.0, 0.0],
                                                  [0.0, 0.0, 0.0]]))

    with open(tmpdir.join('vec2.gz'), 'rb') as fp:
        result = np.frombuffer(fp.read(), dtype='float').reshape([-1, 3])
        np.testing.assert_equal(result, np.array([[1.0, 1.0, 1.0],
                                                  [1.0, 1.0, 1.0],
                                                  [1.0, 1.0, 1.0]]))

    chunkIndexer1 = BinaryPbIndexer.load(tmpdir.join('kvidx1.bin'))
    assert chunkIndexer1.size == 3
    d_id = list(chunkIndexer1.query_handler.header.keys())[0]

    query_doc = jina_pb2.Document()
    query_doc.ParseFromString(chunkIndexer1.query(d_id))
    assert query_doc.text == 'title: this is mode1 from doc1'
    assert query_doc.modality == 'mode1'

    chunkIndexer2 = BinaryPbIndexer.load(tmpdir.join('kvidx2.bin'))
    assert chunkIndexer2.size == 3
    d_id = list(chunkIndexer2.query_handler.header.keys())[0]

    query_doc = jina_pb2.Document()
    query_doc.ParseFromString(chunkIndexer2.query(d_id))
    assert query_doc.text == ' body: this is mode2 from doc1'
    assert query_doc.modality == 'mode2'

    del os.environ['JINA_TEST_FLOW_MULTIMODE_WORKSPACE']

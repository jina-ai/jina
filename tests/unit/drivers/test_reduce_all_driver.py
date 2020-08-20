import os
from typing import List, Dict

import numpy as np

from jina.executors.crafters import BaseSegmenter
from jina.executors.encoders import BaseEncoder
from jina.flow import Flow
from jina.proto.jina_pb2 import Document
from tests import JinaTestCase

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
            if 'mode1' in r:
                output.append([0.0, 0.0, 0.0])
            elif 'mode2' in r:
                output.append([1.0, 1.0, 1.0])

        return np.array(output)


class ReduceAllDriverTestCase(JinaTestCase):
    def test_merge_chunks_with_different_modality(self):
        def input_fn():
            doc1 = Document()
            doc1.id = 1
            doc1.text = 'title: this is mode1 from doc1, body: this is mode2 from doc1'
            doc2 = Document()
            doc2.id = 2
            doc2.text = 'title: this is mode1 from doc2, body: this is mode2 from doc2'
            doc3 = Document()
            doc3.id = 3
            doc3.text = 'title: this is mode1 from doc3, body: this is mode2 from doc3'
            return [doc1, doc2, doc3]

        def validate(req):
            assert len(req.index.docs) == 3
            for doc in req.index.docs:
                assert len(doc.chunks) == 2
                self.assertIn(doc.chunks[0].modality, ['mode1', 'mode2'])
                self.assertIn(doc.chunks[1].modality, ['mode1', 'mode2'])

        flow = Flow().add(name='crafter', uses='MockSegmenter'). \
            add(name='encoder1', uses=os.path.join(cur_dir, 'yaml/mockencoder-mode1.yml')). \
            add(name='encoder2', uses=os.path.join(cur_dir, 'yaml/mockencoder-mode2.yml'), needs=['crafter']). \
            add(name='reducer', uses='- !ReduceAllDriver | {traverse_on: [chunks], depth_range: [0, 1]}',
                needs=['encoder1', 'encoder2'])

        with flow:
            flow.index(input_fn=input_fn, output_fn=validate)

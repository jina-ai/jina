import os
from typing import List, Dict

import numpy as np

from jina.executors.crafters import BaseSegmenter
from jina.executors.encoders import BaseEncoder
from jina.flow import Flow
from jina.proto.jina_pb2 import DocumentProto

cur_dir = os.path.dirname(os.path.abspath(__file__))


class MockSegmenterReduce(BaseSegmenter):

    def craft(self, text: str, *args, **kwargs) -> List[Dict]:
        split = text.split(',')
        chunks = [dict(text=split[0], offset=0, weight=1.0, modality='mode1'),
                  dict(text=split[1], offset=1, weight=1.0, modality='mode2')]
        return chunks


class MockEncoderReduce(BaseEncoder):

    def encode(self, data: str, *args, **kwargs) -> 'np.ndarray':
        output = []
        for r in data:
            if 'mode1' in r:
                output.append([0.0, 0.0, 0.0])
            elif 'mode2' in r:
                output.append([1.0, 1.0, 1.0])

        return np.array(output)


def test_merge_chunks_with_different_modality():
    def input_fn():
        doc1 = DocumentProto()
        doc1.text = 'title: this is mode1 from doc1, body: this is mode2 from doc1'
        doc2 = DocumentProto()
        doc2.text = 'title: this is mode1 from doc2, body: this is mode2 from doc2'
        doc3 = DocumentProto()
        doc3.text = 'title: this is mode1 from doc3, body: this is mode2 from doc3'
        return [doc1, doc2, doc3]

    def validate(req):
        assert len(req.index.docs) == 3
        for doc in req.index.docs:
            assert len(doc.chunks) == 2
            assert doc.chunks[0].modality in ['mode1', 'mode2']
            assert doc.chunks[1].modality in ['mode1', 'mode2']

    flow = Flow().add(name='crafter', uses='MockSegmenterReduce'). \
        add(name='encoder1', uses=os.path.join(cur_dir, 'yaml/mockencoder-mode1.yml')). \
        add(name='encoder2', uses=os.path.join(cur_dir, 'yaml/mockencoder-mode2.yml'), needs=['crafter']). \
        add(name='reducer', uses='- !ReduceAllDriver | {traversal_paths: [c]}',
            needs=['encoder1', 'encoder2'])

    with flow:
        flow.index(input_fn=input_fn, output_fn=validate)


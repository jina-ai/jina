import gzip
import os
import shutil
from typing import List, Dict

import numpy as np

from jina.executors.crafters import BaseSegmenter
from jina.executors.encoders import BaseEncoder
from jina.executors.indexers.keyvalue import BinaryPbIndexer
from jina.flow import Flow
from jina.proto.jina_pb2 import Document

cur_dir = os.path.dirname(os.path.abspath(__file__))


def rm_files(file_paths):
    for file_path in file_paths:
        if os.path.exists(file_path):
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path, ignore_errors=False, onerror=None)


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


def test_flow_with_modalities():
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

    flow = Flow().add(name='crafter', uses='!MockSegmenter'). \
        add(name='encoder1', uses=os.path.join(cur_dir, 'yaml/mockencoder-mode1.yml')). \
        add(name='indexer1', uses=os.path.join(cur_dir, 'yaml/numpy-indexer-1.yml'), needs=['encoder1']). \
        add(name='encoder2', uses=os.path.join(cur_dir, 'yaml/mockencoder-mode2.yml'), needs=['crafter']). \
        add(name='indexer2', uses=os.path.join(cur_dir, 'yaml/numpy-indexer-2.yml')). \
        join(['indexer1', 'indexer2'])

    with flow:
        flow.index(input_fn=input_fn)

    with gzip.open('vec1.gz', 'rb') as fp:
        result = np.frombuffer(fp.read(), dtype='float').reshape([-1, 3])
        np.testing.assert_equal(result, np.array([[0.0, 0.0, 0.0],
                                                  [0.0, 0.0, 0.0],
                                                  [0.0, 0.0, 0.0]]))

    with gzip.open('vec2.gz', 'rb') as fp:
        result = np.frombuffer(fp.read(), dtype='float').reshape([-1, 3])
        np.testing.assert_equal(result, np.array([[1.0, 1.0, 1.0],
                                                  [1.0, 1.0, 1.0],
                                                  [1.0, 1.0, 1.0]]))

    chunkIndexer1 = BinaryPbIndexer(index_filename='chunk1.gz')
    assert len(chunkIndexer1.query_handler.items()) == 3
    for key, pb in chunkIndexer1.query_handler.items():
        for chunk in pb.chunks:
            assert chunk.modality == 'mode1'

    chunkIndexer2 = BinaryPbIndexer(index_filename='chunk2.gz')
    assert len(chunkIndexer2.query_handler.items()) == 3
    for key, pb in chunkIndexer2.query_handler.items():
        for chunk in pb.chunks:
            assert chunk.modality == 'mode2'

    rm_files(['vec1.gz', 'vec2.gz', 'chunk1.gz', 'chunk2.gz',
              'vecidx1.bin', 'vecidx2.bin', 'kvidx1.bin', 'kvidx2.bin'])

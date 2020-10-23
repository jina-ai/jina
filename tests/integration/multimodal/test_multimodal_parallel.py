import pytest
import os
import numpy as np

from jina.flow import Flow
from jina.proto import jina_pb2
from jina.drivers.helper import array2pb, pb2array

NUM_DOCS = 100
cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def multimodal_documents():
    docs = []
    for idx in range(0, NUM_DOCS):
        """
        doc - idx
            |
            | - chunk - blob [idx, idx] - modality1
            | - chunk - blob [idx, idx] - modality2               
        """
        doc = jina_pb2.Document()
        doc.text = f'{idx}'

        for modality in ['modality1', 'modality2']:
            chunk = doc.chunks.add()
            chunk.modality = modality
            chunk.blob.CopyFrom(array2pb(np.array([idx, idx])))
        docs.append(doc)
    return docs


def test_multimodal_parallel(multimodal_documents):
    def validate_response(resp):
        assert len(resp.index.docs) == NUM_DOCS
        for idx, doc in enumerate(resp.index.docs):
            # TODO: Investigate why the shape is [[]]
            np.testing.assert_almost_equal(pb2array(doc.embedding), np.array([[idx, idx, idx, idx]]))

    with Flow().load_config(os.path.join(cur_dir, 'flow-multimodal-parallel.yml')) as index_gt_flow:
        index_gt_flow.index(input_fn=multimodal_documents,
                            output_fn=validate_response)

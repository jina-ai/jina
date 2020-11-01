import os

import numpy as np
import pytest

from jina.proto import jina_pb2
from jina.proto.ndarray.generic import GenericNdArray


@pytest.fixture(scope='function')
def random_workspace(tmp_path):
    os.environ['JINA_TEST_INCREMENTAL_INDEX_WORKSPACE'] = str(tmp_path)
    yield tmp_path
    del os.environ['JINA_TEST_INCREMENTAL_INDEX_WORKSPACE']


def get_duplicate_docs(num_docs=10):
    result = []
    unique_set = set()
    for idx in range(num_docs):
        doc = jina_pb2.Document()
        content = int(idx / 2)
        GenericNdArray(doc.embedding).value = np.array([content])
        doc.text = f'I am doc{content}'
        result.append(doc)
        unique_set.add(content)
    return result, len(unique_set)

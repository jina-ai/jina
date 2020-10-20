import os
import pytest
import numpy as np
from jina.proto import jina_pb2
from jina.drivers.helper import array2pb


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
        doc.embedding.CopyFrom(array2pb(np.array([content])))
        doc.text = f'I am doc{content}'
        result.append(doc)
        unique_set.add(content)
    return result, len(unique_set)



import os

import numpy as np
import pytest

from jina import Document


@pytest.fixture(scope='function')
def random_workspace(tmp_path):
    os.environ['JINA_TEST_INCREMENTAL_INDEX_WORKSPACE'] = str(tmp_path)
    yield tmp_path
    del os.environ['JINA_TEST_INCREMENTAL_INDEX_WORKSPACE']


def get_duplicate_docs(num_docs=10):
    result = []
    for idx in range(num_docs):
        with Document() as doc:
            content = int(idx / 2)
            doc.embedding = np.array([content])
            doc.text = f'I am doc{content}'
            result.append(doc)
    num_uniques = len(set(d.id for d in result))
    return result, num_uniques

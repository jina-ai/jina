import os
import pytest

from jina.flow import Flow
from tests import random_docs

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.skip('TODO: https://github.com/jina-ai/jina/issues/1067')
def test_route():
    docs = random_docs(num_docs=2, chunks_per_doc=2)
    f = (Flow()
         .add(uses='_forward',
              uses_before=os.path.join(cur_dir, 'yaml', 'route.yml'),
              shards=2))

    with f:
        f.index(docs)

    # the code should be running properly
    assert True

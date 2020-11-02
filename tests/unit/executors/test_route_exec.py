import os
from pprint import pprint

import pytest

from jina.executors import BaseExecutor
from jina.flow import Flow
from tests import random_docs

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_load_driver():
    b = BaseExecutor.load_config(os.path.join(cur_dir, 'yaml/route.yml'))
    pprint(b._drivers)

    c = BaseExecutor.load_config('_route')
    assert len(b._drivers['ControlRequest']) == len(c._drivers['ControlRequest'])
    pprint(c._drivers)


@pytest.mark.skip('https://github.com/jina-ai/jina/pull/1070')
def test_route():
    docs = random_docs(num_docs=2, chunks_per_doc=2)
    f = (Flow()
         .add(uses='_pass',
              uses_before=os.path.join(cur_dir, 'yaml', 'route.yml'),
              shards=2))

    with f:
        f.index(docs)

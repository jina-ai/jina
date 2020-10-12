from jina.flow import Flow

from tests import random_docs

from jina.executors import BaseExecutor
import os

cur_dir = os.path.dirname(os.path.abspath(__file__))

def test_load_driver():
    b = BaseExecutor.load_config(os.path.join(cur_dir, 'yaml/route.yml'))
    print(b._drivers)

    c = BaseExecutor.load_config('_route')
    assert len(b._drivers['ControlRequest']) == len(c._drivers['ControlRequest'])
    print(c._drivers)

def test_route():
    docs = random_docs(num_docs=2, chunks_per_doc=2)
    f = (Flow()
         .add(uses='_pass',
              uses_before=os.path.join(cur_dir, 'yaml', 'route.yml'),
              shards=2))

    with f:
        f.index(docs)

test_load_driver()
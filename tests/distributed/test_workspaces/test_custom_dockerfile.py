import os
import numpy as np

from jina import Flow, __default_host__, Document

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_custom_dockerfile():
    f = Flow().add(
        uses='DummyRedisIndexer',
        py_modules='redis_executor.py',
        upload_files=[
            os.path.join(cur_dir, '../../daemon/unit/models/good_ws_custom_dockerfile'),
        ],
        host='localhost:8000',
    )
    with f:
        f.index(
            inputs=(
                Document(text=f'{i}', embedding=np.random.rand(2, 3)) for i in range(5)
            ),
        )
        resp = f.search(inputs=[Document(text='3')], return_results=True)
        assert resp[0].docs[0].matches[0].text == '3'
        assert resp[0].docs[0].matches[0].embedding.shape == (2, 3)

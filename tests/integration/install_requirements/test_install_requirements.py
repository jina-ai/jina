import os
from jina import Flow, DocumentArray

cur_dir = os.path.dirname(__file__)


def test_install_reqs():
    f = Flow().add(install_requirements=True, uses=os.path.join(os.path.join(cur_dir, 'exec'), 'config.yml'))
    with f:
        resp = f.post(on='/', inputs=DocumentArray.empty(2))

    assert len(resp) == 2

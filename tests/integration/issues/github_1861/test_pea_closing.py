import pytest

from jina.executors.encoders import BaseEncoder
from jina.flow import Flow


class ExceptionExecutor(BaseEncoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = 'exception-executor'

    def post_init(self):
        raise Exception


@pytest.mark.timeout(10)
def test_pea_closing():
    with pytest.raises(Exception):
        with Flow().add(uses='!ExceptionExecutor', parallel=3) as f:
            pod1 = f._pod_nodes['pod0']
            assert len(pod1.peas) == 0

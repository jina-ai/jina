import pytest
from jina.flow import Flow
from jina.peapods import Pod
from jina.main.parser import set_pod_parser

"""
Github issue: https://github.com/jina-ai/jina/issues/936
PR solves: https://github.com/jina-ai/jina/issues/935

With a complex Flow structure as in this test, stopping the log server was not properly handled and
the Flow could not properly finish. It resulted in a deadlock.
"""


@pytest.mark.timeout(60)
@pytest.mark.repeat(10)
def test_flow_with_sse_no_deadlock():
    f = Flow(logserver=True). \
        add(uses='BaseExecutor', parallel=2, name='crafter').add(uses='BaseExecutor', parallel=2, name='encoder'). \
        add(uses='BaseExecutor', parallel=2, name='vec_idx').add(uses='BaseExecutor', parallel=2, needs=['gateway'],
                                                                 name='doc_idx'). \
        add(uses='_merge', needs=['vec_idx', 'doc_idx'])
    with f:
        assert hasattr(f, '_sse_logger')
        pass


@pytest.mark.repeat(10)
def test_flow_with_sse_no_deadlock_one_pod():
    f = Flow(logserver=True). \
        add(uses='BaseExecutor', parallel=1, name='crafter')
    with f:
        assert hasattr(f, '_sse_logger')
        pass


@pytest.mark.repeat(10)
def test_pod_with_sse_no_deadlock():
    args = set_pod_parser().parse_args(['--parallel', '4', '--log-sse'])
    p = Pod(args)
    with p:
        pass


@pytest.mark.repeat(10)
def test_pod_with_sse_no_deadlock_thread():
    args = set_pod_parser().parse_args(['--parallel', '4', '--runtime', 'thread', '--log-sse'])
    p = Pod(args)
    with p:
        pass

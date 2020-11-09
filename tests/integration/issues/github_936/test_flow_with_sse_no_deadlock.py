import os

import pytest

from jina.flow import Flow
from jina.parser import set_pod_parser
from jina.peapods import Pod

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
        add(needs=['vec_idx', 'doc_idx'])
    with f:
        assert hasattr(f, '_sse_logger')
        pass


@pytest.mark.timeout(10)
@pytest.mark.repeat(10)
def test_flow_with_sse_no_deadlock_one_pod():
    f = Flow(logserver=True). \
        add(uses='BaseExecutor', parallel=1, name='crafter')
    with f:
        assert hasattr(f, '_sse_logger')
        pass


@pytest.mark.timeout(10)
@pytest.mark.repeat(10)
def test_pod_without_sse_no_parallelism_no_deadlock():
    args = set_pod_parser().parse_args(['--parallel', '1'])
    p = Pod(args)
    with p:
        pass


@pytest.mark.timeout(10)
@pytest.mark.repeat(10)
def test_pod_with_sse_no_parallelism_no_deadlock():
    args = set_pod_parser().parse_args(['--parallel', '1'])
    p = Pod(args)
    with p:
        pass


@pytest.mark.timeout(10)
@pytest.mark.repeat(10)
def test_pod_with_sse_no_deadlock_parallelism():
    args = set_pod_parser().parse_args(['--parallel', '2'])
    p = Pod(args)
    with p:
        pass


@pytest.mark.timeout(10)
@pytest.mark.repeat(10)
def test_pod_with_sse_no_deadlock_log_remote():
    args = set_pod_parser().parse_args(['--parallel', '2', '--log-remote'])
    p = Pod(args)
    with p:
        pass


@pytest.mark.timeout(10)
@pytest.mark.repeat(10)
def test_pod_with_sse_no_deadlock_log_file():
    os.environ['JINA_LOG_FILE'] = 'TXT'
    args = set_pod_parser().parse_args(['--parallel', '2'])
    p = Pod(args)
    with p:
        pass
    del os.environ['JINA_LOG_FILE']


@pytest.mark.timeout(10)
@pytest.mark.repeat(10)
def test_pod_with_sse_no_deadlock_thread():
    args = set_pod_parser().parse_args(['--parallel', '2', '--runtime', 'thread'])
    p = Pod(args)
    with p:
        pass

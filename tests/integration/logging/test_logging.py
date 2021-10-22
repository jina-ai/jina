import os
import pytest

from jina import Flow
from jina.peapods.pods import Pod
from jina.parsers import set_pod_parser
from jina import __resources_path__

NUM_DOCS = 100
cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def test_logging_daemon():
    os.environ['JINA_LOG_CONFIG'] = os.path.join(
        __resources_path__, 'logging.daemon.yml'
    )
    yield
    os.unsetenv('JINA_LOG_CONFIG')


@pytest.mark.parametrize('flow_log_id', [None, 'identity_flow'])
def test_logging(monkeypatch, flow_log_id, test_logging_daemon):
    from fluent import asynchandler as fluentasynchandler

    def mock_emit(obj, record):
        msg = obj.format(record)
        ct = msg['context']
        if ct not in ['JINA', 'PROFILE', 'BaseExecutor']:
            if msg['name'] != 'gateway':
                assert msg['log_id'] == 'identity_flow'
        if msg['name'] == 'gateway':
            assert 'log_id' in msg

    monkeypatch.setattr(fluentasynchandler.FluentHandler, "emit", mock_emit)

    with Flow(identity='identity_flow').add(name='executor1').add(name='executor2'):
        pass


def test_logging_pod(monkeypatch, test_logging_daemon):
    from fluent import asynchandler as fluentasynchandler

    def mock_emit(obj, record):
        msg = obj.format(record)

        ct = msg['context']
        if ct not in ['JINA', 'PROFILE', 'BaseExecutor']:
            assert msg['log_id'] == 'logging_id'
        if msg['name'] == 'gateway':
            assert 'log_id' in msg

    monkeypatch.setattr(fluentasynchandler.FluentHandler, "emit", mock_emit)

    args = set_pod_parser().parse_args(['--identity', 'logging_id'])
    with Pod(args):
        pass

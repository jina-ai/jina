import os
import pytest

from jina.flow import Flow
from jina.peapods.pod import BasePod
from jina.parser import set_pod_parser

NUM_DOCS = 100
cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.parametrize('flow_log_id',
                         [None, 'identity_flow'])
def test_logging(monkeypatch, flow_log_id):
    from fluent import asynchandler as fluentasynchandler

    def mock_emit(obj, record):
        msg = obj.format(record)

        ct = msg['context']
        if ct not in ['JINA', 'PROFILE']:
            if msg['name'] != 'gateway':
                assert msg['log_id'] == 'identity_flow'
        if msg['name'] == 'gateway':
            assert 'log_id' in msg

    monkeypatch.setattr(fluentasynchandler.FluentHandler, "emit", mock_emit)

    with Flow(log_id='identity_flow').add(name='pod1'). \
            add(name='pod2'):
        pass


def test_logging_pod(monkeypatch):
    from fluent import asynchandler as fluentasynchandler

    def mock_emit(obj, record):
        msg = obj.format(record)

        ct = msg['context']
        if ct not in ['JINA', 'PROFILE']:
            assert msg['log_id'] == 'logging_id'
        if msg['name'] == 'gateway':
            assert 'log_id' in msg

    monkeypatch.setattr(fluentasynchandler.FluentHandler, "emit", mock_emit)

    args = set_pod_parser().parse_args(['--log-id', 'logging_id'])
    with BasePod(args):
        pass

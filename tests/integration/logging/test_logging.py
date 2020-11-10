import os
import pytest

from jina.flow import Flow
from jina.peapods.pod import BasePod
from jina.parser import set_pod_parser

NUM_DOCS = 100
cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.parametrize('flow_identity',
                         [None, 'identity_flow'])
def test_logging(monkeypatch, flow_identity):
    from fluent import asynchandler as fluentasynchandler

    if flow_identity:
        flow = Flow(identity=flow_identity)
    else:
        flow = Flow()

    expected_group_id = flow.args.identity
    if flow_identity:
        assert expected_group_id == flow_identity

    def mock_emit(obj, record):
        msg = obj.format(record)

        ct = msg['context']
        if ct not in ['JINA', 'PROFILE']:
            if msg['name'] != 'gateway':
                assert msg['group_id'] == expected_group_id
        if msg['name'] == 'gateway':
            assert 'group_id' in msg

    monkeypatch.setattr(fluentasynchandler.FluentHandler, "emit", mock_emit)

    with flow.add(name='pod1', identity='identity_pod1'). \
            add(name='pod2', identity='identity_pod2'):
        pass


@pytest.mark.parametrize('flow_identity, expected_group_id',
                         [
                             (None, 'identity_pod'),
                             ('identity_flow', 'identity_flow')
                         ])
def test_logging_pod(monkeypatch, flow_identity, expected_group_id):
    from fluent import asynchandler as fluentasynchandler

    def mock_emit(obj, record):
        msg = obj.format(record)

        ct = msg['context']
        if ct not in ['JINA', 'PROFILE']:
            assert msg['group_id'] == expected_group_id
        if msg['name'] == 'gateway':
            assert 'group_id' in msg

    monkeypatch.setattr(fluentasynchandler.FluentHandler, "emit", mock_emit)
    if flow_identity:
        args = set_pod_parser().parse_args(['--flow-identity', flow_identity, '--identity', 'identity_pod'])
    else:
        args = set_pod_parser().parse_args(['--identity', 'identity_pod'])

    with BasePod(args):
        pass

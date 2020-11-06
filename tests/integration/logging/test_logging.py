import os

from jina.flow import Flow

NUM_DOCS = 100
cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_logging(monkeypatch):
    from fluent import asynchandler as fluentasynchandler

    def mock_emit(obj, record):
        msg = obj.format(record)

        ct = msg['context']
        if ct not in ['JINA', 'PROFILE']:
            if 'flow' in ct:
                assert msg['group_id'] == 'identity_flow'
            elif 'pod1' in ct:
                assert msg['group_id'] == 'identity_pod1'
            elif 'pod2' in ct:
                assert msg['group_id'] == 'identity_pod2'

    monkeypatch.setattr(fluentasynchandler.FluentHandler, "emit", mock_emit)

    with Flow(identity='identity_flow').add(name='pod1', identity='identity_pod1').add(name='pod2', identity='identity_pod2') as flow:
        pass

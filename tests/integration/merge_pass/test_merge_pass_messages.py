import time

from jina import Flow
from jina import Document
from jina.executors.crafters import BaseCrafter
from tests import validate_callback


class SlowCrafter(BaseCrafter):
    def craft(self, text, *args, **kwargs):
        time.sleep(2)
        return {'text': text, 'tags': {'id': 'slow'}}


def test_flow_pass(mocker):
    def validate(resp):
        assert len(resp.index.docs) == 1
        # only the second part of the message is passed by _pass
        assert resp.index.docs[0].tags['id'] == 'slow'

    f = (
        Flow()
        .add(name='pod0', uses='_pass')
        .add(name='pod1', uses='!SlowCrafter', needs=['gateway'])
        .add(name='pod2', uses='_pass', needs=['pod0', 'pod1'])
    )
    doc = Document()
    doc.text = 'text'
    mock = mocker.Mock()
    with f:
        f.index([doc], on_done=mock)

    mock.assert_called_once()
    validate_callback(mock, validate)


def test_flow_merge(mocker):
    def validate(resp):
        assert len(resp.index.docs) == 2
        assert resp.index.docs[0].id == resp.index.docs[1].id

    f = (
        Flow()
        .add(name='pod0', uses='_pass')
        .add(name='pod1', uses='_pass', needs=['gateway'])
        .add(name='pod2', uses='_merge', needs=['pod0', 'pod1'])
    )
    doc = Document()
    doc.text = 'text'
    mock = mocker.Mock()
    with f:
        f.index([doc], on_done=mock)

    mock.assert_called_once()
    validate_callback(mock, validate)


def test_flow_merge_root(mocker):
    def validate(resp):
        assert len(resp.index.docs) == 2
        assert resp.index.docs[0].id == resp.index.docs[1].id

    f = (
        Flow()
        .add(name='pod0', uses='_pass')
        .add(name='pod1', uses='_pass', needs=['gateway'])
        .add(name='pod2', uses='_merge_root', needs=['pod0', 'pod1'])
    )
    doc = Document()
    doc.text = 'text'
    mock = mocker.Mock()
    with f:
        f.index([doc], on_done=mock)

    mock.assert_called_once()
    validate_callback(mock, validate)


def test_flow_merge_chunks(mocker):
    def validate(resp):
        assert len(resp.index.docs) == 1

    f = (
        Flow()
        .add(name='pod0', uses='_pass')
        .add(name='pod1', uses='_pass', needs=['gateway'])
        .add(name='pod2', uses='_merge_chunks', needs=['pod0', 'pod1'])
    )
    doc = Document()
    doc.text = 'text'
    mock = mocker.Mock()
    with f:
        f.index([doc], on_done=mock)

    mock.assert_called_once()
    validate_callback(mock, validate)

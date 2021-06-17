import os
from pathlib import Path

import pytest

from daemon.models import PeaModel, DaemonID
from daemon.models.enums import UpdateOperation
from daemon.stores.partial import PartialStore, PartialPeaStore, PartialFlowStore
from jina import helper, Flow
from jina.helper import ArgNamespace
from jina.parsers import set_pea_parser

cur_dir = Path(__file__).parent


@pytest.fixture(autouse=True)
def patch_os_kill(monkeypatch):
    monkeypatch.setattr(os, "kill", lambda *args, **kwargs: None)


@pytest.fixture()
def partial_pea_store():
    partial_pea_store = PartialPeaStore()
    yield partial_pea_store
    partial_pea_store.delete()


@pytest.fixture()
def partial_flow_store():
    partial_flow_store = PartialFlowStore()
    yield partial_flow_store
    partial_flow_store.delete()


@pytest.mark.timeout(5)
def test_partialstore_delete(monkeypatch, mocker):
    close_mock = mocker.Mock()
    kill_mock = mocker.Mock()
    monkeypatch.setattr(os, "kill", kill_mock)
    partial_store = PartialStore()

    partial_store.object = close_mock
    partial_store.delete()
    kill_mock.assert_called()
    close_mock.close.assert_called()


def test_peastore_add(partial_pea_store):
    partial_store_item = partial_pea_store.add(
        args=ArgNamespace.kwargs2namespace(PeaModel().dict(), set_pea_parser())
    )
    assert partial_store_item
    assert partial_pea_store.object

    assert (
        partial_store_item.arguments['docker_kwargs']['extra_hosts'][
            'host.docker.internal'
        ]
        == 'host-gateway'
    )


def test_flowstore_add(monkeypatch, partial_flow_store):
    flow_id = DaemonID('jflow')
    port_expose = helper.random_port()
    partial_store_item = partial_flow_store.add(
        filename=f'{cur_dir}/flow.yml', id=flow_id, port_expose=port_expose
    )

    assert partial_store_item
    assert isinstance(partial_flow_store.object, Flow)
    assert 'pod1' in partial_store_item.yaml_source
    assert partial_flow_store.object.identity['pod1'] == flow_id.jid
    assert partial_flow_store.object.args.port_expose == port_expose


def test_flowstore_update(partial_flow_store, mocker):
    partial_flow_store.add(
        filename=f'{cur_dir}/flow.yml',
        id=DaemonID('jflow'),
        port_expose=helper.random_port(),
    )

    update_mock = mocker.Mock()
    dump_mock = mocker.Mock()
    partial_flow_store.object.rolling_update = update_mock
    partial_flow_store.object.dump = dump_mock

    partial_flow_store.update(
        kind=UpdateOperation.ROLLING_UPDATE, dump_path='', pod_name='pod1', shards=1
    )
    partial_flow_store.update(
        kind=UpdateOperation.DUMP, dump_path='', pod_name='pod1', shards=1
    )

    update_mock.assert_called()
    dump_mock.assert_called()

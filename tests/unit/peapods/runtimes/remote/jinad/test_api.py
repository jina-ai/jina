import os
import uuid

import mock
import pytest

from jina.logging.logger import JinaLogger
from jina.parsers import set_pea_parser
from jina.peapods.runtimes.jinad.client import (
    PodDaemonClient,
    PeaDaemonClient,
    WorkspaceDaemonClient,
)

logger = JinaLogger(context='test-remote')
yaml_path = os.path.dirname(os.path.abspath(__file__))
pod_api = PodDaemonClient(host='0.0.0.0', port=8000, logger=logger)
pea_api = PeaDaemonClient(host='0.0.0.0', port=8000, logger=logger)
workspace_api = WorkspaceDaemonClient(host='0.0.0.0', port=8000, logger=logger)


@mock.patch('requests.get')
def test_jinad_is_alive(mocker):
    mocker.return_value.status_code = 200
    assert pea_api.alive

    mocker.return_value.status_code = 404
    assert not pod_api.alive


@mock.patch('requests.get')
@pytest.mark.parametrize('api', [pea_api, pod_api, workspace_api])
def test_api_get(mocker, api):
    _an_id = uuid.uuid4()
    mocker.return_value.status_code = 200
    mocker.return_value.json = lambda: {'1': '2'}
    assert api.get(id=_an_id) == {'1': '2'}

    mocker.return_value.status_code = 404
    assert api.get(id=_an_id) == {'1': '2'}


@mock.patch('requests.delete')
@pytest.mark.parametrize('api', [pea_api, pod_api, workspace_api])
def test_api_delete(mocker, api):
    mocker.return_value.status_code = 200
    assert api.delete(id='abcd')

    mocker.return_value.status_code = 404
    assert not api.delete(id='abcd')


@mock.patch('requests.post')
@pytest.mark.parametrize('api', [pea_api, pod_api])
def test_peapod_create(mocker, api):
    args = set_pea_parser().parse_args([])
    mocker.return_value.status_code = 201
    mocker.return_value.json.return_value = 'abcd'
    assert api.post(args) == 'abcd'

    mocker.return_value.status_code = 404
    assert not api.post(args)


@mock.patch('requests.post')
def test_workspace_create(mocker):
    _dependencies = [__file__]
    _w_id = uuid.uuid4()
    mocker.return_value.status_code = 201
    mocker.return_value.json.return_value = 'abcd'
    assert workspace_api.post(_dependencies, _w_id) == 'abcd'

    mocker.return_value.status_code = 404
    assert not workspace_api.post(_dependencies, _w_id)


def test_daemonize_id():
    an_id = uuid.uuid4()
    assert pea_api._daemonize_id(an_id) == f'jworkspace-{an_id}'
    assert pea_api._daemonize_id('abcd') == 'jworkspace-abcd'
    assert pea_api._daemonize_id(an_id, 'pea') == f'jpea-{an_id}'

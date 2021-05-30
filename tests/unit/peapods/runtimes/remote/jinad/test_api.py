import os

import mock
import pytest

from jina.logging.logger import JinaLogger
from jina.parsers import set_pea_parser
from jina.peapods.runtimes.jinad.client import (
    DaemonClient,
    PodDaemonClient,
    PeaDaemonClient,
)

logger = JinaLogger(context='test-remote')
yaml_path = os.path.dirname(os.path.abspath(__file__))
jinad_api = DaemonClient(host='0.0.0.0', port=8000, logger=logger)
pod_api = PodDaemonClient(host='0.0.0.0', port=8000, logger=logger)
pea_api = PeaDaemonClient(host='0.0.0.0', port=8000, logger=logger)


@mock.patch('requests.get')
def test_jinad_is_alive(mocker):
    mocker.return_value.status_code = 200
    assert jinad_api.is_alive

    mocker.return_value.status_code = 404
    assert not jinad_api.is_alive


@mock.patch('requests.delete')
@pytest.mark.parametrize('api', [pea_api, pod_api, jinad_api])
def test_podapi_delete(mocker, api):
    mocker.return_value.status_code = 200
    assert api.delete(remote_id='abcd')

    mocker.return_value.status_code = 404
    assert not api.delete(remote_id='abcd')


@mock.patch('requests.post')
@pytest.mark.parametrize('api', [pea_api, pod_api, jinad_api])
def test_peapod_create(mocker, api):
    args = set_pea_parser().parse_args([])
    mocker.return_value.status_code = 201
    mocker.return_value.json.return_value = 'abcd'
    assert api.create(args) == 'abcd'

    mocker.return_value.status_code = 404
    assert not api.create(args)

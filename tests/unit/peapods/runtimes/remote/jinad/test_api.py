import argparse
import os

import mock
import pytest

from jina.logging import JinaLogger
from jina.peapods.runtimes.jinad.api import JinadAPI, PodJinadAPI, PeaJinadAPI

logger = JinaLogger(context='test-remote')
yaml_path = os.path.dirname(os.path.abspath(__file__))
jinad_api = JinadAPI(host='0.0.0.0', port=8000, logger=logger)
pod_api = PodJinadAPI(host='0.0.0.0', port=8000, logger=logger)
pea_api = PeaJinadAPI(host='0.0.0.0', port=8000, logger=logger)


def test_fetch_files_from_yaml_pods():
    pea_args = {
        'head': None,
        'tail': None,
        'peas': [
            {
                'name': 'encode',
                'uses': f'{yaml_path}/yamls/encoder.yml',
                'py_modules': None,
                'uses_before': None,
                'uses_after': None
            },
            {
                'name': 'index',
                'uses': f'{yaml_path}/yamls/indexer.yml',
                'py_modules': None,
                'uses_before': None,
                'uses_after': None
            },
        ]
    }
    _uses_files, _pymodule_files = fetch_files_from_yaml(pea_args, logger)
    assert _uses_files == {f'{yaml_path}/yamls/encoder.yml',
                           f'{yaml_path}/yamls/indexer.yml'}
    assert _pymodule_files == {f'{yaml_path}/yamls/dummy.py'}


def test_fetch_files_from_yaml_pea():
    pea_args = {
        'name': 'encode',
        'uses': f'{yaml_path}/yamls/encoder.yml',
        'py_modules': None,
        'uses_before': None,
        'uses_after': None
    }
    _uses_files, _pymodule_files = fetch_files_from_yaml(pea_args, logger)
    assert _uses_files == {f'{yaml_path}/yamls/encoder.yml'}
    assert _pymodule_files == {f'{yaml_path}/yamls/dummy.py'}


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
    args = argparse.Namespace()
    mocker.return_value.status_code = 201
    mocker.return_value.json.return_value = 'abcd'
    assert api.create(args) == 'abcd'

    mocker.return_value.status_code = 404
    assert not api.create(args)

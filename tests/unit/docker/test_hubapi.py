import json
from logging import getLogger

import mock
import pytest
import requests

from jina.docker import hubapi
from jina.docker.hubapi import _docker_auth
from jina.docker.hubapi import _fetch_access_token
from jina.docker.hubapi import _list

sample_manifest = {
    'manifest': [
        {
            'name': 'Dummy MWU Encoder',
            'description': 'a minimum working unit of a containerized encoder, used for tutorial only',
            'type': 'pod',
            'author': 'Jina AI Dev-Team (dev-team@jina.ai)',
            'url': 'https://jina.ai',
            'documentation': 'https://github.com/jina-ai/jina-hub',
            'version': '0.0.52',
            'vendor': 'Jina AI Limited',
            'license': 'apache-2.0',
            'avatar': None,
            'platform': [
                'linux/amd64'
            ],
            'keywords': [
                'toy',
                'example'
            ],
            'manifest_version': 1,
            'update': 'nightly',
            'kind': 'encoder'
        }
    ]
}


@mock.patch('jina.docker.hubapi.urlopen')
def test_hubapi_list(mocker):
    mocker.return_value.__enter__.return_value.read.return_value = json.dumps(sample_manifest)
    result = _list(logger=getLogger(),
                   image_name='Dummy MWU Encoder',
                   image_kind='encoder',
                   image_type='pod',
                   image_keywords=['toy'])

    mocker.assert_called_once()
    assert result[0]['name'] == 'Dummy MWU Encoder'
    assert result[0]['version'] == '0.0.52'
    assert result[0]['kind'] == 'encoder'


@mock.patch('jina.docker.hubapi.JAML.load')
def test_fetch_access_token(mocker):
    token_string = json.dumps({'access_token': 'dummy_token'})
    token_json = json.loads(token_string)
    mocker.return_value = token_json
    _fetch_access_token(logger=getLogger())


@pytest.fixture(scope='function')
def docker_jaml_token():
    token_string = json.dumps({'hubapi': {'url': 'dummy_url', 'docker_auth': 'dummy_auth'}})
    token_json = json.loads(token_string)
    return token_json


def test_docker_auth_success(mocker, docker_jaml_token):
    mock_load = mocker.patch.object(hubapi.JAML, 'load', autospec=True)
    mock_load.return_value = docker_jaml_token

    mock_access_token = mocker.patch.object(hubapi, '_fetch_access_token', autospec=True)
    mock_access_token.return_value = 'dummy_token'

    mock_response = mocker.patch.object(requests, 'get', autospec=True)
    import base64
    encoded_usr = base64.b64encode(b'dummy_user').decode('ascii')
    encoded_psw = base64.b64encode(b'dummy_password').decode('ascii')
    mock_response.return_value.status_code = 200
    mock_response.return_value.text = json.dumps({'docker_username': encoded_usr, 'docker_password': encoded_psw})

    # Verify the fetched creds are as expected
    fetch_cred = _docker_auth(logger=getLogger())
    assert fetch_cred['docker_username'] == base64.b64decode(encoded_usr).decode('ascii')
    assert fetch_cred['docker_password'] == base64.b64decode(encoded_psw).decode('ascii')


def test_docker_auth_failure(mocker, docker_jaml_token):
    mock_load = mocker.patch.object(hubapi.JAML, 'load', autospec=True)
    mock_load.return_value = docker_jaml_token

    mock_access_token = mocker.patch.object(hubapi, '_fetch_access_token', autospec=True)
    mock_access_token.return_value = 'dummy_token'

    mock_response = mocker.patch.object(requests, 'get', autospec=True)
    mock_response.return_value.status_code = 403
    mock_response.return_value.text = json.dumps({'message': 'Missing Authentication Token'})

    # If no token is fetched, docker auth fails
    fetch_cred = _docker_auth(logger=getLogger())
    assert fetch_cred is None

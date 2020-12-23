import json
from logging import getLogger

import json
import mock
import pytest

from jina.docker.hubapi import _list
from jina.docker.hubapi import JAML
from jina.docker.hubapi import _fetch_access_token

sample_manifest = {
    'manifest': [
        {
            "name": "Dummy MWU Encoder",
            "description": "a minimum working unit of a containerized encoder, used for tutorial only",
            "type": "pod",
            "author": "Jina AI Dev-Team (dev-team@jina.ai)",
            "url": "https://jina.ai",
            "documentation": "https://github.com/jina-ai/jina-hub",
            "version": "0.0.52",
            "vendor": "Jina AI Limited",
            "license": "apache-2.0",
            "avatar": None,
            "platform": [
                "linux/amd64"
            ],
            "keywords": [
                "toy",
                "example"
            ],
            "manifest_version": 1,
            "update": "nightly",
            "kind": "encoder"
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
    token_string = json.dumps({'access_token':'dummy_token'})
    token_json = json.loads(token_string)
    mocker.return_value = token_json
    _fetch_access_token(logger=getLogger())
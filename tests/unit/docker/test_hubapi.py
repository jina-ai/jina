import mock
import pytest

from logging import getLogger
from jina.docker.hubapi import _list, _push


def mock_list_api(url, params):
    _list_api = mock.Mock()
    _list_api.status_code = 200
    _list_api.json.return_value = {
        "manifest": [
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
                "platform": ["linux/amd64"],
                "keywords": ["toy", "example"],
                "manifest_version": 1,
                "update": "nightly",
                "kind": "encoder",
            }
        ]
    }
    return _list_api


@mock.patch("jina.docker.hubapi.requests")
def test_hubapi_list(mocker):
    mocker.get.side_effect = mock_list_api
    result = _list(
        logger=getLogger(),
        name="Dummy MWU Encoder",
        kind="encoder",
        type_="pod",
        keywords=["toy"],
    )

    mocker.get.assert_called_once()
    assert result.json()["manifest"][0]["name"] == "Dummy MWU Encoder"
    assert result.json()["manifest"][0]["version"] == "0.0.52"
    assert result.json()["manifest"][0]["kind"] == "encoder"

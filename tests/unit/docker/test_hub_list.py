import json
import mock

from jina.docker.hubio import HubIO
from jina.parsers.hub import set_hub_list_parser


def test_hub_list_local_with_submodule():
    args = set_hub_list_parser().parse_args(['--local-only'])
    response = HubIO(args).list()
    assert len(response) > 1


@mock.patch('jina.docker.hubapi.remote.urlopen')
def test_hub_list_keywords(mocker):
    mocker.return_value.__enter__.return_value.read.return_value = json.dumps(
        [{'name': 'foo'}, {'name': 'bar'}]
    )

    args = set_hub_list_parser().parse_args(['--keywords', 'numeric'])
    response = HubIO(args).list()
    numeric_count = len(response)

    mocker.assert_called_once()
    assert numeric_count > 1

    args = set_hub_list_parser().parse_args(['--keywords', 'numeric', 'randjojd'])
    response = HubIO(args).list()
    combined_count = len(response)

    assert mocker.call_count == 2
    assert combined_count > 1

    # Making sure both arguments are --keywords are considered as `either or`
    assert combined_count >= numeric_count


@mock.patch('jina.docker.hubapi.remote.urlopen')
def test_hub_list_nonexisting_kind(mocker):
    mocker.return_value.__enter__.return_value.read.return_value = json.dumps([])

    args = set_hub_list_parser().parse_args(['--kind', 'blah'])
    response = HubIO(args).list()

    mocker.assert_called_once()
    assert not response

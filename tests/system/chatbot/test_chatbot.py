import os

import pytest

from jina import Flow, Document
from jina.types.document.generators import from_csv
from jina.helloworld.chatbot.app import hello_world
from jina.parsers.helloworld import set_hw_chatbot_parser
from jina.helloworld.chatbot.app import download_data
from jina.helloworld.chatbot.my_executors import MyTransformer, MyIndexer
from tests import validate_callback


@pytest.fixture
def helloworld_args(tmpdir):
    return set_hw_chatbot_parser().parse_args(
        [
            '--workdir',
            str(tmpdir),
            '--unblock-query-flow',
        ]
    )


@pytest.fixture
def expected_result():
    return '''It's not completely up to you.'''


@pytest.fixture
def flow(tmpdir):
    return Flow().add(uses=MyTransformer, parallel=1).add(uses=MyIndexer, workspace=str(tmpdir))


def test_chatbot(helloworld_args, expected_result, flow, mocker):
    """Regression test for chatbot example."""
    hello_world(helloworld_args)
    # def validate_response(resp):
    #     assert len(resp.data.docs) == 1
    #     for doc in resp.data.docs:
    #         assert len(doc.matches) == 10
    #
    #
    # targets = {
    #     'covid-csv': {
    #         'url': helloworld_args.index_data_url,
    #         'filename': os.path.join(helloworld_args.workdir, 'dataset.csv'),
    #     }
    # }
    #
    # mock_on_done = mocker.Mock()
    # mock_on_fail = mocker.Mock()
    #
    # # download the data
    # download_data(targets, helloworld_args.download_proxy, task_name='download csv data')
    # with flow, open(targets['covid-csv']['filename']) as fp:
    #     flow.index(from_csv(fp, field_resolver={'question': 'text'}))
    #     flow.search(
    #         inputs=Document(text='Is my dog safe from virus'),
    #         on_done=mock_on_done,
    #         on_fail=mock_on_fail,
    #         parameters={'top_k': 10},
    #     )
    #
    #     mock_on_fail.assert_not_called()
    #     validate_callback(mock_on_done, validate_response)

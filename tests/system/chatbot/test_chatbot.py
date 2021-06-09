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
            '--port-expose',
            '8080',
            '--unblock-query-flow',
            '--parallel',
            '1',
        ]
    )


def test_chatbot(helloworld_args, tmpdir, mocker):
    """Regression test for chatbot example."""
    hello_world(helloworld_args)

    def validate_response(resp):
        assert len(resp.data.docs) == 1
        for doc in resp.data.docs:
            assert len(doc.matches) == 1
            assert (
                'there is currently no evidence that pets such as dogs or cats can be'
                in doc.matches[0].tags['answer']
            )

    targets = {
        'covid-csv': {
            'url': helloworld_args.index_data_url,
            'filename': os.path.join(helloworld_args.workdir, 'dataset.csv'),
        }
    }

    mock_on_done = mocker.Mock()
    mock_on_fail = mocker.Mock()

    download_data(
        targets, helloworld_args.download_proxy, task_name='download csv data'
    )
    f = (
        Flow()
        .add(uses=MyTransformer, parallel=1)
        .add(uses=MyIndexer, workspace=str(tmpdir))
    )
    with f, open(targets['covid-csv']['filename']) as fp:
        f.index(from_csv(fp, field_resolver={'question': 'text'}))
        f.search(
            inputs=Document(content='Is my dog safe from virus'),
            on_done=mock_on_done,
            on_fail=mock_on_fail,
            parameters={'top_k': 10},
        )

        mock_on_fail.assert_not_called()
        validate_callback(mock_on_done, validate_response)

import os
from jina import Flow, Document
from jina.executors import BaseExecutor
from jina.parsers import set_pea_parser
from jina.peapods.peas import BasePea

from tests import validate_callback

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_load_executor_with_custom_driver():
    with BaseExecutor.load_config(
        os.path.join(cur_dir, 'yaml/test-executor-with-custom-driver.yml')
    ) as be:
        assert be._drivers['IndexRequest'][0].__class__.__name__ == 'DummyEncodeDriver'


def test_load_pod_with_custom_driver():
    args = set_pea_parser().parse_args(
        ['--uses', os.path.join(cur_dir, 'yaml/test-executor-with-custom-driver.yml')]
    )
    with BasePea(args):
        # load success with no error
        pass


def test_load_flow_with_custom_driver(mocker):
    mock = mocker.Mock()

    def validate(req):
        assert len(req.docs) == 1
        assert req.docs[0].text == 'hello from DummyEncodeDriver'

    with Flow().add(
        uses=os.path.join(cur_dir, 'yaml/test-executor-with-custom-driver.yml')
    ) as f:
        f.index([Document()], on_done=mock)

    validate_callback(mock, validate)

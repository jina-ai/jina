from pathlib import Path

from jina import Flow, Document
from jina.executors import BaseExecutor
from jina.parser import set_pea_parser
from jina.peapods.peas import BasePea

cur_dir = Path(__file__).parent


def test_load_executor_with_custom_driver():
    with BaseExecutor.load_config(str(cur_dir / 'yaml/test-executor-with-custom-driver.yml')) as be:
        assert be._drivers['IndexRequest'][0].__class__.__name__ == 'DummyEncodeDriver'


def test_load_pod_with_custom_driver():
    args = set_pea_parser().parse_args(['--uses', str(cur_dir / 'yaml/test-executor-with-custom-driver.yml')])
    with BasePea(args):
        # load success with no error
        pass


def test_load_flow_with_custom_driver():
    with Flow().add(uses=str(cur_dir / 'yaml/test-executor-with-custom-driver.yml')) as f:
        f.index([Document()])

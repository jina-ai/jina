import os

import pytest
from pkg_resources import resource_filename

from jina.drivers import BaseDriver
from jina.drivers.control import ControlReqDriver
from jina.drivers.search import KVSearchDriver
from jina.executors import BaseExecutor
from jina.jaml import JAML
from jina.parsers import set_pod_parser
from jina.peapods import Pod

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_load_yaml1(tmpdir):
    with open(os.path.join(cur_dir, 'yaml/test-driver.yml'), encoding='utf8') as fp:
        a = JAML.load(fp)

    assert isinstance(a[0], KVSearchDriver)
    assert isinstance(a[1], ControlReqDriver)
    assert isinstance(a[2], BaseDriver)

    with open(os.path.join(tmpdir, 'test_driver.yml'), 'w', encoding='utf8') as fp:
        JAML.dump(a[0], fp)

    with open(os.path.join(tmpdir, 'test_driver.yml'), encoding='utf8') as fp:
        b = JAML.load(fp)

    assert isinstance(b, KVSearchDriver)
    assert b._executor_name == a[0]._executor_name


def test_load_cust_with_driver():
    a = BaseExecutor.load_config(
        os.path.join(cur_dir, 'mwu-encoder/mwu_encoder_driver.yml')
    )
    assert a._drivers['ControlRequest'][0].__class__.__name__ == 'MyAwesomeDriver'
    p = set_pod_parser().parse_args(
        ['--uses', os.path.join(cur_dir, 'mwu-encoder/mwu_encoder_driver.yml')]
    )
    with Pod(p):
        # will print a cust task_name from the driver when terminate
        pass


def test_pod_new_api_from_kwargs():
    a = BaseExecutor.load_config(
        os.path.join(cur_dir, 'mwu-encoder/mwu_encoder_driver.yml')
    )
    assert a._drivers['ControlRequest'][0].__class__.__name__ == 'MyAwesomeDriver'

    args = set_pod_parser().parse_args(
        ['--uses', os.path.join(cur_dir, 'mwu-encoder/mwu_encoder_driver.yml')]
    )
    with Pod(args):
        # will print a cust task_name from the driver when terminate
        pass


@pytest.mark.parametrize('random_workspace_name', ['JINA_TEST_EXEC_WITH_DRIVER'])
def test_load_yaml2(test_metas):
    a = BaseExecutor.load_config(
        os.path.join(cur_dir, 'yaml/test-exec-with-driver.yml')
    )
    assert len(a._drivers) == 2
    # should be able to auto fill in ControlRequest
    assert 'ControlRequest' in a._drivers
    a.save_config()
    p = a.config_abspath
    b = BaseExecutor.load_config(p)
    assert a._drivers == b._drivers
    a.touch()
    a.save()
    c = BaseExecutor.load(a.save_abspath)
    assert a._drivers == c._drivers


@pytest.mark.parametrize(
    'yaml_path, name, expected',
    [
        ('executors._clear.yml', 'clear', 6),
        ('executors._concat.yml', 'concat', 6),
        ('executors._eval_pr.yml', 'eval_pr', 2),
        ('executors._logforward.yml', 'logforward', 6),
        ('executors._merge.yml', 'merge', 6),
        ('executors._merge_chunks.yml', 'merge_chunks', 6),
        ('executors._merge_eval.yml', 'merge_eval', 6),
        ('executors._merge_matches.yml', 'merge_matches', 6),
        ('executors._pass.yml', 'forward', 6),
    ],
)
def test_resource_executor(yaml_path, name, expected):
    a = BaseExecutor.load_config(
        resource_filename('jina', '/'.join(('resources', yaml_path)))
    )
    assert a.name == name
    assert len(a._drivers) == expected


def test_multiple_executor():
    from jina.executors.encoders import BaseEncoder
    from jina.executors.indexers import BaseIndexer
    from jina.executors.rankers import Chunk2DocRanker
    from jina.executors.crafters import BaseCrafter

    class D1(BaseEncoder):
        pass

    d1 = D1()
    assert len(d1._drivers) == 6

    class D2(BaseIndexer):
        pass

    d2 = D2('dummy.bin')
    assert len(d2._drivers) == 1

    class D3(Chunk2DocRanker):
        pass

    d3 = D3()
    assert len(d3._drivers) == 2

    class D4(BaseCrafter):
        pass

    d4 = D4()
    assert len(d4._drivers) == 6

    class D5(BaseCrafter):
        pass

    d5 = D5()
    assert len(d5._drivers) == 6

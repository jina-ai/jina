from argparse import ArgumentParser

import pytest

from daemon.helper import get_enum_defaults, handle_enums, pod_to_namespace, pea_to_namespace
from daemon.models import PeaModel, SinglePodModel, ParallelPodModel
from jina import __default_host__
from jina.enums import BetterEnum, RuntimeBackendType, PeaRoleType


class SampleEnum(BetterEnum):
    A = 1
    B = 2


parser = ArgumentParser()
parser.add_argument('--arg1', default=SampleEnum.A)
parser.add_argument('--arg2', default=5)


def test_enum_defaults():
    res = get_enum_defaults(parser=parser)
    assert 'arg1' in res
    assert res['arg1'].name == 'A'
    assert res['arg1'].value == 1
    assert 'arg2' not in res


def test_handle_enums():
    args = {'arg1': 2, 'arg2': 6}
    res = handle_enums(args, parser)
    assert 'arg1' in res
    assert res['arg1'] == SampleEnum.B
    assert res['arg2'] == args['arg2']

    args = {'arg1': 3, 'arg2': 6}
    with pytest.raises(ValueError):
        handle_enums(args, parser)


def test_single_pod_to_namespace():
    pod_args = pod_to_namespace(
        SinglePodModel(
            name='mypod',
            pea_role=3,
            runtime_backend=0,
            log_config='blah',
            host='3.19.298.2'
        )
    )
    assert 'identity' in pod_args
    assert 'port_expose' in pod_args
    assert 'uses' in pod_args
    assert 'parallel' in pod_args

    assert 'name' in pod_args
    assert pod_args.name == 'mypod'

    assert 'pea_role' in pod_args
    # This tests number to enum conversion
    assert pod_args.pea_role == PeaRoleType.PARALLEL

    assert 'runtime_backend' in pod_args
    # This tests number to enum conversion
    assert pod_args.runtime_backend == RuntimeBackendType.THREAD

    assert 'log_config' in pod_args
    # we explicitly remove log_config
    assert pod_args.log_config != 'blah'

    assert 'host' in pod_args
    # we explicitly set host to __default_host__
    assert pod_args.host == __default_host__


def test_parallel_pod_to_namespace():
    pod_args = pod_to_namespace(
        ParallelPodModel(
            head=SinglePodModel(),
            tail=SinglePodModel(),
            peas=[
                SinglePodModel(
                    name='pod0',
                    host='3.19.298.2',
                    log_config='blah0'
                ),
                SinglePodModel(
                    name='pod1',
                    host='3.19.298.2',
                    log_config='blah1'
                )
            ]
        )
    )
    assert 'identity' in pod_args['head']
    assert 'identity' in pod_args['tail']
    assert 'identity' in pod_args['peas'][0]
    assert 'identity' in pod_args['peas'][1]

    assert 'port_expose' in pod_args['head']
    assert 'port_expose' in pod_args['tail']
    assert 'port_expose' in pod_args['peas'][0]
    assert 'port_expose' in pod_args['peas'][1]

    assert 'name' in pod_args['peas'][0]
    assert pod_args['peas'][0].name == 'pod0'

    assert 'name' in pod_args['peas'][1]
    assert pod_args['peas'][1].name == 'pod1'

    assert 'host' in pod_args['peas'][0]
    # we explicitly set host to __default_host__
    assert pod_args['peas'][0].host == __default_host__

    assert 'host' in pod_args['peas'][1]
    # we explicitly set host to __default_host__
    assert pod_args['peas'][1].host == __default_host__

    assert 'log_config' in pod_args['peas'][0]
    # we explicitly remove log_config
    assert pod_args['peas'][0].log_config != 'blah0'

    assert 'log_config' in pod_args['peas'][1]
    # we explicitly remove log_config
    assert pod_args['peas'][1].log_config != 'blah1'


def test_pea_to_namespace():
    pea_args = pea_to_namespace(
        PeaModel(
            name='mypea',
            py_modules='abc.py',
            runtime_cls='RESTRuntime',
            show_exc_info=True,
            pea_role=2,
            log_config='blah'
        )
    )
    assert 'identity' in pea_args
    assert 'port_expose' in pea_args
    assert 'uses' in pea_args
    assert 'py_modules' in pea_args
    assert 'parallel' not in pea_args

    assert 'name' in pea_args
    assert pea_args.name == 'mypea'

    assert 'py_modules' in pea_args
    assert pea_args.py_modules == 'abc.py'

    assert 'runtime_cls' in pea_args
    assert pea_args.runtime_cls == 'RESTRuntime'

    assert 'show_exc_info' in pea_args
    assert pea_args.show_exc_info

    assert 'pea_role' in pea_args
    assert pea_args.pea_role == PeaRoleType.TAIL

    assert 'log_config' in pea_args
    # we explicitly remove log_config
    assert pea_args.log_config != 'blah'

    assert 'host' in pea_args
    # we explicitly set host to __default_host__
    assert pea_args.host == __default_host__

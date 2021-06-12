import os
from pathlib import Path

import numpy as np
import pytest

from jina import Executor
from jina.excepts import BadFlowYAMLVersion
from jina import Flow
from jina.jaml import JAML
from jina.jaml.parsers import get_supported_versions
from jina.parsers.flow import set_flow_parser
from jina.types.document.generators import from_ndarray

cur_dir = Path(__file__).parent


def test_load_flow_from_empty_yaml():
    with open(cur_dir / 'yaml' / 'dummy-flow.yml') as fp:
        JAML.load(fp)

    with open(cur_dir / 'yaml' / 'dummy-flow.yml') as fp:
        Flow.load_config(fp)


def test_support_versions():
    assert get_supported_versions(Flow) == ['1', 'legacy']


def test_load_legacy_and_v1():
    Flow.load_config('yaml/flow-legacy-syntax.yml')
    Flow.load_config('yaml/flow-v1-syntax.yml')

    # this should fallback to v1
    Flow.load_config('yaml/flow-v1.0-syntax.yml')

    with pytest.raises(BadFlowYAMLVersion):
        Flow.load_config('yaml/flow-v99-syntax.yml')


def test_add_needs_inspect(tmpdir):
    f1 = (
        Flow()
        .add(name='pod0', needs='gateway')
        .add(name='pod1', needs='gateway')
        .inspect()
        .needs(['pod0', 'pod1'])
    )
    with f1:
        f1.index(from_ndarray(np.random.random([5, 5])), on_done=print)

    f2 = Flow.load_config('yaml/flow-v1.0-syntax.yml')

    with f2:
        f2.index(from_ndarray(np.random.random([5, 5])), on_done=print)

    assert f1 == f2


def test_load_dump_load(tmpdir):
    """TODO: Dumping valid yaml is out of scope of PR#1442, to do in separate PR"""
    f1 = Flow.load_config('yaml/flow-legacy-syntax.yml')
    f1.save_config(str(Path(tmpdir) / 'a0.yml'))
    f2 = Flow.load_config('yaml/flow-v1.0-syntax.yml')
    f2.save_config(str(Path(tmpdir) / 'a1.yml'))


def test_load_flow_with_port():
    f = Flow.load_config('yaml/test-flow-port.yml')
    with f:
        assert f.port_expose == 12345


def test_load_flow_from_cli():
    a = set_flow_parser().parse_args(['--uses', 'yaml/test-flow-port.yml'])
    f = Flow.load_config(a.uses)
    with f:
        assert f.port_expose == 12345


def test_load_flow_from_yaml():
    with open(cur_dir.parent / 'yaml' / 'test-flow.yml') as fp:
        _ = Flow.load_config(fp)


def test_flow_yaml_dump(tmpdir):
    f = Flow()
    f.save_config(os.path.join(str(tmpdir), 'test1.yml'))
    fl = Flow.load_config(os.path.join(str(tmpdir), 'test1.yml'))
    assert f.args.inspect == fl.args.inspect


def test_flow_yaml_from_string():
    f1 = Flow.load_config('yaml/flow-v1.0-syntax.yml')
    with open(str(cur_dir / 'yaml' / 'flow-v1.0-syntax.yml')) as fp:
        str_yaml = fp.read()
        assert isinstance(str_yaml, str)
        f2 = Flow.load_config(str_yaml)
        assert f1 == f2

    f3 = Flow.load_config(
        '!Flow\nversion: 1.0\npods: [{name: ppp0, uses: _merge}, name: aaa1]'
    )
    assert 'ppp0' in f3._pod_nodes.keys()
    assert 'aaa1' in f3._pod_nodes.keys()
    assert f3.num_pods == 2


def test_flow_uses_from_dict():
    class DummyEncoder(Executor):
        pass

    d1 = {'jtype': 'DummyEncoder', 'metas': {'name': 'dummy1'}}
    with Flow().add(uses=d1):
        pass

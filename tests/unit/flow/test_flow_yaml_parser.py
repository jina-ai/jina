from pathlib import Path

import numpy as np
import pytest

from jina import Flow, AsyncFlow
from jina.enums import FlowOptimizeLevel
from jina.excepts import BadFlowYAMLVersion
from jina.flow import BaseFlow
from jina.jaml import JAML
from jina.jaml.parsers import get_supported_versions
from jina.parsers.flow import set_flow_parser
from tests import rm_files

cur_dir = Path(__file__).parent


def test_load_flow_from_empty_yaml():
    with open(cur_dir / 'yaml' / 'dummy-flow.yml') as fp:
        JAML.load(fp)

    with open(cur_dir / 'yaml' / 'dummy-flow.yml') as fp:
        Flow.load_config(fp)


def test_support_versions():
    assert get_supported_versions(Flow) == ['1', 'legacy']
    assert get_supported_versions(AsyncFlow) == ['1', 'legacy']
    assert get_supported_versions(BaseFlow) == ['1', 'legacy']


def test_load_legacy_and_v1():
    Flow.load_config('yaml/flow-legacy-syntax.yml')
    Flow.load_config('yaml/flow-v1-syntax.yml')

    # this should fallback to v1
    Flow.load_config('yaml/flow-v1.0-syntax.yml')

    with pytest.raises(BadFlowYAMLVersion):
        Flow.load_config('yaml/flow-v99-syntax.yml')


def test_add_needs_inspect(tmpdir):
    f1 = (Flow().add(name='pod0', needs='gateway').add(name='pod1', needs='gateway').inspect().needs(['pod0', 'pod1']))
    with f1:
        f1.index_ndarray(np.random.random([5, 5]), on_done=print)

    f2 = Flow.load_config('yaml/flow-v1.0-syntax.yml')

    with f2:
        f2.index_ndarray(np.random.random([5, 5]), on_done=print)

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
        a = Flow.load_config(fp)

def test_flow_yaml_dump():
    f = Flow(logserver_config=str(cur_dir.parent / 'yaml' / 'test-server-config.yml'),
             optimize_level=FlowOptimizeLevel.IGNORE_GATEWAY,
             no_gateway=True)
    f.save_config('test1.yml')

    fl = Flow.load_config('test1.yml')
    assert f.args.logserver_config == fl.args.logserver_config
    assert f.args.optimize_level == fl.args.optimize_level
    rm_files(['test1.yml'])

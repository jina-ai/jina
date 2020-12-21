from pathlib import Path

import numpy as np
import pytest

from jina import Flow
from jina.excepts import BadFlowYAMLVersion
from jina.flow.yaml_parser import get_supported_versions
from jina.jaml import JAML


def test_load_flow_from_empty_yaml():
    with open('yaml/dummy-flow.yml') as fp:
        JAML.load(fp)

    with open('yaml/dummy-flow.yml') as fp:
        Flow.load_config(fp)


def test_support_versions():
    assert get_supported_versions() == ['1', 'legacy']


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

import filecmp
from pathlib import Path

import numpy as np
import pytest

from jina import Flow
from jina.excepts import BadFlowYAMLVersion
from jina.flow.parser import get_support_versions


def test_support_versions():
    assert get_support_versions() == ['1', 'legacy']


def test_load_legacy_and_v1():
    Flow.load_config('yaml/flow-legacy-syntax.yml')
    Flow.load_config('yaml/flow-v1-syntax.yml')

    # this should fallback to v1
    Flow.load_config('yaml/flow-v1.0-syntax.yml')

    with pytest.raises(BadFlowYAMLVersion):
        Flow.load_config('yaml/flow-v99-syntax.yml')


def test_add_needs_inspect(tmpdir):
    f1 = (Flow().add(name='pod0', needs='gateway').add(name='pod1', needs='gateway').inspect().needs(['pod0', 'pod1']))
    f1.plot(Path(tmpdir) / 'from_python.jpg')
    with f1:
        f1.index_ndarray(np.random.random([5, 5]), output_fn=print)

    f2 = Flow.load_config('yaml/flow-v1.0-syntax.yml')
    f2.plot(Path(tmpdir) / 'from_yaml.jpg')
    assert filecmp.cmp(Path(tmpdir) / 'from_python.jpg',
                       Path(tmpdir) / 'from_yaml.jpg')

    with f2:
        f2.index_ndarray(np.random.random([5, 5]), output_fn=print)

    assert f1 == f2


def test_load_dump_load(tmpdir):
    f1 = Flow.load_config('yaml/flow-legacy-syntax.yml')
    f1.save_config(Path(tmpdir) / 'a0.yml')
    f2 = Flow.load_config('yaml/flow-v1.0-syntax.yml')
    f2.save_config(Path(tmpdir) / 'a1.yml')

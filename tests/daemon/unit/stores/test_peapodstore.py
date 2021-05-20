import pytest

from daemon.stores import PeaStore, PodStore
from jina import Executor
from jina.parsers import set_pea_parser, set_pod_parser


@pytest.mark.parametrize(
    'parser, store', [(set_pea_parser, PeaStore), (set_pod_parser, PodStore)]
)
def test_peastore_add(parser, store):
    p_args = parser().parse_args([])
    s = store()
    s.add(p_args)
    assert len(s) == 1
    assert p_args.identity in s
    s.delete(p_args.identity)
    assert not s


@pytest.mark.parametrize(
    'parser, store', [(set_pea_parser, PeaStore), (set_pod_parser, PodStore)]
)
def test_peastore_multi_add(parser, store):
    s = store()
    for j in range(5):
        p_args = parser().parse_args([])
        s.add(p_args)
        assert len(s) == j + 1
        assert p_args.identity in s
    s.clear()
    assert not s


@pytest.mark.parametrize(
    'parser, store', [(set_pea_parser, PeaStore), (set_pod_parser, PodStore)]
)
def test_peapod_store_add_bad(parser, store):
    class BadCrafter(Executor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            raise NotImplementedError

    p_args = parser().parse_args(['--uses', 'BadCrafter'])
    s = store()
    with pytest.raises(Exception):
        s.add(p_args)
    assert not s

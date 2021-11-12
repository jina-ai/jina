import pytest

from jina.peapods.pods import Pod
from jina.parsers import set_pod_parser
from jina.excepts import RuntimeFailToStart, ScalingFails


@pytest.fixture
def pod_args():
    return set_pod_parser().parse_args(['--replicas', '3', '--name', 'test'])


@pytest.mark.asyncio
async def test_scale_given_replicas_greater_than_num_peas_success(pod_args):
    # trigger scale up and success
    with Pod(pod_args) as p:
        assert len(p.peas_args['peas']) == 3
        await p.scale(replicas=5)
        assert p.replica_set.num_peas == 5
        assert len(p.peas_args['peas']) == 5


@pytest.mark.asyncio
async def test_scale_given_replicas_equal_to_num_peas(pod_args):
    # trigger scale number equal to current num_peas
    with Pod(pod_args) as p:
        assert len(p.peas_args['peas']) == 3
        await p.scale(replicas=3)
        assert p.replica_set.num_peas == 3
        assert len(p.peas_args['peas']) == 3


@pytest.mark.asyncio
async def test_scale_given_replicas_less_than_num_peas_success(pod_args):
    # trigger scale down and success
    with Pod(pod_args) as p:
        assert len(p.peas_args['peas']) == 3
        await p.scale(replicas=1)
        assert p.replica_set.num_peas == 1
        assert len(p.peas_args['peas']) == 1

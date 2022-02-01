import pytest

from jina.orchestrate.deployments import Deployment
from jina.parsers import set_deployment_parser


@pytest.fixture
def pod_args():
    return set_deployment_parser().parse_args(['--replicas', '3', '--name', 'test'])


@pytest.mark.asyncio
async def test_scale_given_replicas_greater_than_num_pods_success(pod_args):
    # trigger scale up and success
    with Deployment(pod_args) as p:
        assert len(p.pods_args['pods'][0]) == 3
        await p.scale(replicas=5)
        assert p.shards[0].num_pods == 5
        assert len(p.pods_args['pods'][0]) == 5


@pytest.mark.asyncio
async def test_scale_given_replicas_equal_to_num_pods(pod_args):
    # trigger scale number equal to current num_pods
    with Deployment(pod_args) as p:
        assert len(p.pods_args['pods'][0]) == 3
        await p.scale(replicas=3)
        assert p.shards[0].num_pods == 3
        assert len(p.pods_args['pods'][0]) == 3


@pytest.mark.asyncio
async def test_scale_given_replicas_less_than_num_pods_success(pod_args):
    # trigger scale down and success
    with Deployment(pod_args) as p:
        assert len(p.pods_args['pods'][0]) == 3
        await p.scale(replicas=1)
        assert p.shards[0].num_pods == 1
        assert len(p.pods_args['pods'][0]) == 1

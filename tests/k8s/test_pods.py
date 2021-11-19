import pytest

from jina.parsers import set_pod_parser
from jina.peapods.pods.k8s import K8sPod


@pytest.mark.asyncio
async def test_regular_prod(
    test_executor_image, k8s_cluster, load_images_in_kind, logger, test_dir: str
):
    args = set_pod_parser().parse_args(
        [
            '--name',
            'test-pod',
            '--k8s-namespace',
            'default',
            '--shards',
            '2',
            '--replicas',
            '2',
            '--uses-before',
            f'docker://{test_executor_image}',
            '--uses-after',
            f'docker://{test_executor_image}',
        ]
    )
    with K8sPod(args) as pod:
        # check that head deployment exists, is ready and has tthree containers
        # check that 2 shard deployments with 2 replicas exist
        # check that uses_before/uses_after adress match
        # send a request and verify response
        pass


# create a gateway and check that there is no head and gateway is reachable

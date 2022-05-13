import os

import pytest

from jina.orchestrate.deployments import Deployment


@pytest.mark.parametrize(
    'device_str, replicas, expected',
    [
        ['1', 1, None],  # wont trigger device RB
        ['1', 2, None],  # wont trigger device RB
        ['1,2', 2, None],  # wont trigger device RB
        ['RR', 2, {0: 0, 1: 1}],
        ['RR', 5, {0: 0, 1: 1, 2: 2, 3: 0, 4: 1}],
        ['RR1:', 5, {0: 1, 1: 2, 2: 1, 3: 2, 4: 1}],
        ['RR0:2', 5, {0: 0, 1: 1, 2: 0, 3: 1, 4: 0}],
        ['RR1:2', 2, {0: 1, 1: 1}],
        ['RR1:2', 1, {0: 1}],
    ],
)
def test_cuda_assignment(device_str, replicas, expected):
    os.environ['CUDA_TOTAL_DEVICES'] = str(3)
    actual = Deployment._roundrobin_cuda_device(device_str, replicas)
    assert actual == expected

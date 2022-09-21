import os

import pytest

from jina.orchestrate.deployments import Deployment


@pytest.fixture()
def cuda_total_devices(request):
    old_cuda_total_devices = os.environ.get('CUDA_TOTAL_DEVICES', None)
    os.environ['CUDA_TOTAL_DEVICES'] = str(request.param)
    yield
    if old_cuda_total_devices is not None:
        os.environ['CUDA_TOTAL_DEVICES'] = old_cuda_total_devices
    else:
        os.unsetenv('CUDA_TOTAL_DEVICES')


@pytest.mark.parametrize(
    'device_str, replicas, expected, cuda_total_devices',
    [
        ['1', 1, None, 3],  # wont trigger device RB
        ['1', 2, None, 3],  # wont trigger device RB
        ['1,2', 2, None, 3],  # wont trigger device RB
        ['RR', 2, {0: 0, 1: 1}, 3],
        ['RR', 5, {0: 0, 1: 1, 2: 2, 3: 0, 4: 1}, 3],
        ['RR1:', 5, {0: 1, 1: 2, 2: 1, 3: 2, 4: 1}, 3],
        ['RR0:2', 5, {0: 0, 1: 1, 2: 0, 3: 1, 4: 0}, 3],
        ['RR1:2', 2, {0: 1, 1: 1}, 3],
        ['RR1:2', 1, {0: 1}, 3],
        ['RR0,2,3', 3, {0: 0, 1: 2, 2: 3}, 4],
        ['RR0,2,3', 5, {0: 0, 1: 2, 2: 3, 3: 0, 4: 2}, 4],
    ], indirect=['cuda_total_devices']
)
def test_cuda_assignment(device_str, replicas, expected, cuda_total_devices):
    actual = Deployment._roundrobin_cuda_device(device_str, replicas)
    assert actual == expected

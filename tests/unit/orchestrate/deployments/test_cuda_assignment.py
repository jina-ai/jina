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
        ['RR2', 2, {0: 2, 1: 2}, 3],
        ['RRUUID1', 2, {0: 'UUID1', 1: 'UUID1'}, 3],
        ['RR1:2', 1, {0: 1}, 3],
        ['RR0,2,3', 3, {0: 0, 1: 2, 2: 3}, 4],
        ['RR0,2,3', 5, {0: 0, 1: 2, 2: 3, 3: 0, 4: 2}, 4],
        [
            'RRUUID1,UUID2,UUID3',
            5,
            {0: 'UUID1', 1: 'UUID2', 2: 'UUID3', 3: 'UUID1', 4: 'UUID2'},
            4,
        ],
        [
            'RRGPU-0aaaaaaa-74d2-7297-d557-12771b6a79d5,GPU-0bbbbbbb-74d2-7297-d557-12771b6a79d5,GPU-0ccccccc-74d2-7297-d557-12771b6a79d5,GPU-0ddddddd-74d2-7297-d557-12771b6a79d5',
            5,
            {
                0: 'GPU-0aaaaaaa-74d2-7297-d557-12771b6a79d5',
                1: 'GPU-0bbbbbbb-74d2-7297-d557-12771b6a79d5',
                2: 'GPU-0ccccccc-74d2-7297-d557-12771b6a79d5',
                3: 'GPU-0ddddddd-74d2-7297-d557-12771b6a79d5',
                4: 'GPU-0aaaaaaa-74d2-7297-d557-12771b6a79d5',
            },
            4,
        ],
    ],
    indirect=['cuda_total_devices'],
)
def test_cuda_assignment(device_str, replicas, expected, cuda_total_devices):
    actual = Deployment._roundrobin_cuda_device(device_str, replicas)
    assert actual == expected

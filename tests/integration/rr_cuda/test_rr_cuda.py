import os

import pytest

from jina import Flow, Executor, requests, DocumentArray, Document


@pytest.fixture()
def cuda_total_devices(request):
    old_cuda_total_devices = os.environ.get('CUDA_TOTAL_DEVICES', None)
    os.environ['CUDA_TOTAL_DEVICES'] = str(request.param)
    yield
    if old_cuda_total_devices is not None:
        os.environ['CUDA_TOTAL_DEVICES'] = old_cuda_total_devices
    else:
        os.unsetenv('CUDA_TOTAL_DEVICES')


@pytest.fixture()
def cuda_visible_devices(request):
    old_cuda_total_devices = os.environ.get('CUDA_VISIBLE_DEVICES', None)
    if request.param is not None:
        os.environ['CUDA_VISIBLE_DEVICES'] = str(request.param)
    yield
    if old_cuda_total_devices is not None:
        os.environ['CUDA_VISIBLE_DEVICES'] = old_cuda_total_devices
    else:
        os.unsetenv('CUDA_VISIBLE_DEVICES')


@pytest.mark.parametrize(
    'cuda_total_devices, cuda_visible_devices, env',
    [[3, 'RR', None], [3, None, {'CUDA_VISIBLE_DEVICES': 'RR'}]],
    indirect=['cuda_total_devices', 'cuda_visible_devices'],
)
def test_cuda_assignment(cuda_total_devices, cuda_visible_devices, env):
    class MyCUDAUserExecutor(Executor):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.cuda_visible_devices = os.environ['CUDA_VISIBLE_DEVICES']

        @requests
        def foo(self, **kwargs):
            return DocumentArray(
                [
                    Document(
                        tags={'cuda_visible_devices': str(self.cuda_visible_devices)}
                    )
                ]
            )

    f = Flow().add(uses=MyCUDAUserExecutor, env=env or {}, replicas=3)
    with f:
        ret = f.post(on='/', inputs=DocumentArray.empty(50), request_size=1)
        cuda_visible_devices = set([doc.tags['cuda_visible_devices'] for doc in ret])

    assert cuda_visible_devices == {'0', '1', '2'}

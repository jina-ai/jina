import os

import pytest

from jina import Flow, Executor, requests


class DummyDumpExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pod_name = kwargs['runtime_args']['name']

    @requests(on='/dump')
    def custom_dump(self, parameters, **kwargs):
        dump_path = parameters['dump_path']
        shards = parameters['shards']
        with open(f'{dump_path}/{self.pod_name}', 'w') as f:
            f.write(f'{self.pod_name},{shards}')


@pytest.mark.timeout(5)
def test_dump_is_called(mocker, tmp_path):
    done_mock = mocker.Mock()
    flow = (
        Flow()
        .add(
            name='pod1',
            uses=DummyDumpExecutor,
        )
        .add(
            name='pod2',
            uses=DummyDumpExecutor,
        )
    )
    with flow:
        flow.dump(pod_name='pod1', dump_path=str(tmp_path), shards=1, on_done=done_mock)
        assert os.path.exists(f'{tmp_path}/pod1')
        assert not os.path.exists(f'{tmp_path}/pod2')
        _validate_dump(tmp_path, 'pod1', 1.0)
        done_mock.assert_called()


def _validate_dump(tmp_path, pod_name, shards):
    with open(f'{tmp_path}/{pod_name}', 'r') as f:
        params = f.read().split(',')
        assert params[0] == pod_name
        assert params[1] == str(shards)

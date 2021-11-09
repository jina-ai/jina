import os
import time

import pytest

from jina import Flow, Executor, Document, DocumentArray, requests

cur_dir = os.path.dirname(os.path.abspath(__file__))
IMG_NAME = 'jina/scale-executor'


class ScalableExecutor(Executor):
    def __init__(self, allow_failure=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.replica_id = self.runtime_args.replica_id
        self.shard_id = self.runtime_args.shard_id
        if self.replica_id > 3 and allow_failure:
            raise Exception(f' I fail when scaling above 4')

    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.tags['replica_id'] = self.replica_id
            doc.tags['shard_id'] = self.shard_id


@pytest.fixture(scope='module')
def docker_image_built():
    import docker

    client = docker.from_env()
    client.images.build(path=os.path.join(cur_dir, 'scale-executor'), tag=IMG_NAME)
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()


@pytest.fixture
def pod_params(request):
    num_replicas, scale_to, shards = request.param
    return num_replicas, scale_to, shards


@pytest.fixture
def flow_with_zed_runtime(pod_params):
    num_replicas, scale_to, shards = pod_params
    return Flow().add(
        name='executor',
        uses=ScalableExecutor,
        uses_with={'allow_failure': scale_to > num_replicas},
        replicas=num_replicas,
        shards=shards,
        polling='ANY',
    )


@pytest.fixture
def flow_with_container_runtime(pod_params):
    num_replicas, scale_to, shards = pod_params
    return Flow().add(
        name='executor',
        uses=f'docker://{IMG_NAME}',
        replicas=num_replicas,
        uses_with={'allow_failure': scale_to > num_replicas},
        shards=shards,
        polling='ANY',
    )


@pytest.fixture(params=['flow_with_zed_runtime', 'flow_with_container_runtime'])
def flow_with_runtime(request):
    return request.getfixturevalue(request.param)


@pytest.mark.parametrize('pod_params', [(2, 3, 1), (5, 4, 2)], indirect=True)
def test_scale_success(flow_with_runtime, pod_params):
    num_replicas, scale_to, shards = pod_params
    with flow_with_runtime as f:
        ret1 = f.index(
            inputs=DocumentArray([Document() for _ in range(200)]),
            return_results=True,
            request_size=10,
        )
        f.scale(pod_name='executor', replicas=scale_to)
        ret2 = f.index(
            inputs=DocumentArray([Document() for _ in range(200)]),
            return_results=True,
            request_size=10,
        )

        assert len(ret1) == 20
        replica_ids = set()
        for r in ret1:
            assert len(r.docs) == 10
            for replica_id in r.docs.get_attributes('tags__replica_id'):
                replica_ids.add(replica_id)

        assert replica_ids == set(range(num_replicas))

        assert len(ret2) == 20
        replica_ids = set()
        for r in ret2:
            assert len(r.docs) == 10
            for replica_id in r.docs.get_attributes('tags__replica_id'):
                replica_ids.add(replica_id)

        assert replica_ids == set(range(scale_to))


# @pytest.mark.parametrize('pod_params', [(2, 3, 1), (5, 4, 2)], indirect=True)
# def test_scale_failure_zedruntime(flow_with_zed_runtime, pod_params):
#     num_replicas, scale_to, shards = pod_params
#     with flow_with_zed_runtime as f:
#         ret1 = f.index(
#             inputs=DocumentArray([Document() for _ in range(200)]),
#             return_results=True,
#             request_size=10,
#         )
#         with pytest.raises(Exception):
#             f.scale(pod_name='executor', replicas=5)
#         ret2 = f.index(
#             inputs=DocumentArray([Document() for _ in range(200)]),
#             return_results=True,
#             request_size=10,
#         )
#
#     assert len(ret1) == 20
#     replica_ids = set()
#     for r in ret1:
#         assert len(r.docs) == 10
#         for replica_id in r.docs.get_attributes('tags__replica_id'):
#             replica_ids.add(replica_id)
#
#     assert replica_ids == {0, 1}
#
#     assert len(ret2) == 20
#     replica_ids = set()
#     for r in ret2:
#         assert len(r.docs) == 10
#         for replica_id in r.docs.get_attributes('tags__replica_id'):
#             replica_ids.add(replica_id)
#
#     assert replica_ids == {0, 1}


# @pytest.mark.parametrize('shards', [1, 2])
# def test_scale_failure_containerruntime(docker_image_built, shards):
#     f = Flow().add(
#         name='executor',
#         uses=f'docker://{img_name}',
#         replicas=2,
#         shards=shards,
#         polling='ANY',
#     )
#     with f:
#         ret1 = f.index(
#             inputs=DocumentArray([Document() for _ in range(200)]),
#             return_results=True,
#             request_size=10,
#         )
#         with pytest.raises(Exception):
#             f.scale(pod_name='executor', replicas=5)
#         ret2 = f.index(
#             inputs=DocumentArray([Document() for _ in range(200)]),
#             return_results=True,
#             request_size=10,
#         )
#
#     assert len(ret1) == 20
#     replica_ids = set()
#     for r in ret1:
#         assert len(r.docs) == 10
#         for replica_id in r.docs.get_attributes('tags__replica_id'):
#             replica_ids.add(replica_id)
#
#     assert replica_ids == {0, 1}
#
#     assert len(ret2) == 20
#     replica_ids = set()
#     for r in ret2:
#         assert len(r.docs) == 10
#         for replica_id in r.docs.get_attributes('tags__replica_id'):
#             replica_ids.add(replica_id)
#
#     assert replica_ids == {0, 1}

import pytest

from jina import Flow, Document, DocumentArray


@pytest.mark.timeout(3600)
@pytest.mark.parametrize('shards', [1, 2])
@pytest.mark.parametrize('new_replicas', [3, 4])
def test_k8s_scale(
    k8s_cluster,
    scale_executor_image,
    load_images_in_kind,
    set_test_pip_version,
    shards,
    new_replicas,
):
    flow = Flow(
        name='test-flow-scale',
        port_expose=9090,
        infrastructure='K8S',
        protocol='http',
        timeout_ready=120000,
    ).add(
        name='test_executor',
        shards=shards,
        replicas=2,
        uses=scale_executor_image,
        timeout_ready=360000,
    )
    with flow as f:
        ret1 = f.index(
            inputs=DocumentArray([Document() for _ in range(200)]),
            return_results=True,
            request_size=10,
        )
        f.scale(pod_name='executor', replicas=new_replicas)
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

    assert replica_ids == {0, 1}

    assert len(ret2) == 20
    replica_ids = set()
    for r in ret2:
        assert len(r.docs) == 10
        for replica_id in r.docs.get_attributes('tags__replica_id'):
            replica_ids.add(replica_id)

    assert replica_ids == set(range(new_replicas))


@pytest.mark.timeout(3600)
@pytest.mark.parametrize('shards', [1, 2])
@pytest.mark.parametrize('new_replicas', [3, 4])
def test_k8s_scale_fails(
    k8s_cluster,
    scale_executor_image,
    load_images_in_kind,
    set_test_pip_version,
    shards,
    new_replicas,
):
    flow = Flow(
        name='test-flow-scale',
        port_expose=9090,
        infrastructure='K8S',
        protocol='http',
        timeout_ready=120000,
    ).add(
        name='test_executor',
        shards=shards,
        replicas=2,
        uses=scale_executor_image,
        timeout_ready=360000,
    )
    with flow as f:
        ret1 = f.index(
            inputs=DocumentArray([Document() for _ in range(200)]),
            return_results=True,
            request_size=10,
        )
        with pytest.raises(Exception):
            f.scale(pod_name='executor', replicas=5)
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

    assert replica_ids == {0, 1}

    assert len(ret2) == 20
    replica_ids = set()
    for r in ret2:
        assert len(r.docs) == 10
        for replica_id in r.docs.get_attributes('tags__replica_id'):
            replica_ids.add(replica_id)

    assert replica_ids == {0, 1}

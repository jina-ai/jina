# import os
# import time
# import pytest
#
# from daemon.clients import JinaDClient, AsyncJinaDClient
# from jina import Client, Document, DocumentArray, __default_host__
#
# cur_dir = os.path.dirname(os.path.abspath(__file__))
# IMG_NAME = 'jina/scalable-executor'
# HOST = __default_host__
# PORT = 8000
#
#
# @pytest.fixture
# def jinad_client():
#     return JinaDClient(host=HOST, port=PORT)
#
#
# @pytest.fixture
# def async_jinad_client():
#     return AsyncJinaDClient(host=HOST, port=PORT)
#
#
# @pytest.fixture(scope='function')
# def docker_image_built():
#     import docker
#
#     client = docker.from_env()
#     client.images.build(
#         path=os.path.join(cur_dir, 'executors/scalable_executor'),
#         tag=IMG_NAME,
#     )
#     client.close()
#     yield
#     time.sleep(2)
#     client = docker.from_env()
#     client.containers.prune()
#
#
# @pytest.mark.parametrize(
#     'pod_params',  # (num_replicas, scale_to, shards)
#     [
#         (1, 2, 1)
#     ],
# )
# def test_scale_remote_flow(docker_image_built, pod_params, jinad_client):
#     num_replicas, scale_to, shards = pod_params
#     flow_id = None
#
#     workspace_id = jinad_client.workspaces.create(
#         paths=[
#             cur_dir,
#             os.path.join(cur_dir, '../test_scale_remote_executors/executors.py'),
#         ]
#     )
#     assert workspace_id
#     flow_id = jinad_client.flows.create(workspace_id=workspace_id, filename='flow1.yml')
#     flow_id = jinad_client.flows.create(
#         workspace_id=workspace_id,
#         filename='flow-scalable.yml',
#     )
#
#         ret1 = Client(port=12345).index(
#             inputs=DocumentArray([Document() for _ in range(200)]),
#             return_results=True,
#             request_size=10,
#         )
#         jinad_client.flows.scale(id=flow_id, pod_name='executor', replicas=scale_to)
#         ret2 = Client(port=12345).index(
#             inputs=DocumentArray([Document() for _ in range(200)]),
#             return_results=True,
#             request_size=10,
#         )
#
#         assert len(ret1) == 20
#         replica_ids = set()
#         for r in ret1:
#             assert len(r.docs) == 10
#             for replica_id in r.docs.get_attributes('tags__replica_id'):
#                 replica_ids.add(replica_id)
#
#         assert replica_ids == set(range(num_replicas))
#
#         assert len(ret2) == 20
#         replica_ids = set()
#         for r in ret2:
#             assert len(r.docs) == 10
#             for replica_id in r.docs.get_attributes('tags__replica_id'):
#                 replica_ids.add(replica_id)
#
#         assert replica_ids == set(range(scale_to))
#     finally:
#         if flow_id:
#             assert jinad_client.flows.delete(flow_id), 'Flow termination failed'
#             print(f'Remote Flow {flow_id} successfully terminated')

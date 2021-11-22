import pytest

from jina import Document, DocumentArray, Client
from jina.clients.request import request_generator
from jina.parsers import set_pod_parser, set_gateway_parser
from jina.peapods.networking import GrpcConnectionPool
from jina.peapods.pods.k8s import K8sPod
from jina.peapods.pods.k8slib import kubernetes_tools
from jina.peapods.pods.k8slib.kubernetes_client import K8sClients
from jina.types.message import Message


def test_regular_pod(
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
            '--uses',
            f'docker://{test_executor_image}',
            '--uses-before',
            f'docker://{test_executor_image}',
            '--uses-after',
            f'docker://{test_executor_image}',
        ]
    )
    with K8sPod(args) as pod:
        k8s_clients = K8sClients()
        pods = k8s_clients.core_v1.list_namespaced_pod(
            namespace='default',
        )
        deployments = k8s_clients.apps_v1.list_namespaced_deployment(
            namespace='default',
        )
        label_dicts = [item.spec.template.metadata.labels for item in deployments.items]

        # check that three deployments exist (head, shard_0, shard_1)
        assert len(label_dicts) == 3
        assert (
            len(
                [
                    label_dict
                    for label_dict in label_dicts
                    if label_dict['pea_type'] == 'worker'
                ]
            )
            == 2
        )
        assert (
            len(
                [
                    label_dict
                    for label_dict in label_dicts
                    if label_dict['pea_type'] == 'head'
                ]
            )
            == 1
        )
        assert any(label_dict['shard_id'] == '0' for label_dict in label_dicts)
        assert any(label_dict['shard_id'] == '1' for label_dict in label_dicts)
        assert all(
            label_dict['jina_pod_name'] == 'test-pod' for label_dict in label_dicts
        )

        # check that five pods exist (head, shard0/rep0, shard0/rep1, shard1/rep0, shard1/rep1)
        assert len(pods.items) == 5
        # check that head has three containers (head/uses_before/uses_after), workers have only one
        for item in pods.items:
            if item.metadata.labels['pea_type'] == 'head':
                assert len(item.spec.containers) == 3
                head_name = item.metadata.name
            else:
                assert len(item.spec.containers) == 1

        # expose the head port and send a request
        with kubernetes_tools.get_port_forward_contextmanager(
            namespace='default', pod_name=head_name, port_expose=8081
        ):
            response = GrpcConnectionPool.send_messages_sync(
                [_create_test_data_message()],
                f'localhost:8081',
            )
            assert len(response.response.docs) == 1
            assert response.response.docs[0].text == 'client'
            assert 'traversed-executors' in response.response.docs[0].tags


def test_gateway_pod(k8s_cluster, load_images_in_kind, logger, test_dir: str):
    args = set_gateway_parser().parse_args(
        [
            '--name',
            'gateway',
            '--k8s-namespace',
            'default',
            '--port-expose',
            '8080',
            '--graph-description',
            '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}',
            '--pods-addresses',
            '{"pod0": ["0.0.0.0:8081"]}',
        ]
    )
    with K8sPod(args) as pod:
        k8s_clients = K8sClients()
        pods = k8s_clients.core_v1.list_namespaced_pod(
            namespace='default',
        )
        deployments = k8s_clients.apps_v1.list_namespaced_deployment(
            namespace='default',
        )
        label_dicts = [item.spec.template.metadata.labels for item in deployments.items]

        # check that one deployments exist
        assert len(label_dicts) == 1
        assert (
            len(
                [
                    label_dict
                    for label_dict in label_dicts
                    if label_dict['pea_type'] == 'gateway'
                ]
            )
            == 1
        )
        # check that one pod exists
        assert len(pods.items) == 1
        # check that head has one container
        for item in pods.items:
            assert len(item.spec.containers) == 1

        # expose the head port and send a request
        with kubernetes_tools.get_port_forward_contextmanager(
            namespace='default', port_expose=8080
        ):

            client_kwargs = dict(
                host='localhost',
                port=8080,
            )
            client = Client(**client_kwargs)
            client.show_progress = True

            def inputs():
                for i in range(1):
                    yield Document(text=f'{i}')

            response = client.post(
                '/index', inputs=inputs, request_size=1, return_results=True
            )

            print(f'got result {response}')

            # response = GrpcConnectionPool.send_messages_sync(
            #     [_create_test_data_message()],
            #     f'localhost:8081',
            # )
            # assert len(response.response.docs) == 1
            # assert response.response.docs[0].text == 'client'
            # assert 'traversed-executors' in response.response.docs[0].tags


def _create_test_data_message():
    req = list(request_generator('/index', DocumentArray([Document(text='client')])))[0]
    msg = Message(None, req)
    return msg

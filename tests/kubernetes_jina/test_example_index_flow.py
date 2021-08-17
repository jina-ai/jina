import pytest

from jina import Flow
from .k8s_testing_tools.testing_tools import KindClusterWithTestClient


@pytest.fixture()
def k8s_index_flow(executor_image) -> Flow:
    test_executor_image_name = executor_image.tags[0]
    test_executor_image_name = 'localhost:5000/' + test_executor_image_name
    index_flow = (
        Flow(name='index-flow', port_expose=8080, protocol='http')
        .add(
            name='segmenter',
            uses=test_executor_image_name,
            uses_with={'name': 'segmenter'}
        ).add(
            name='textencoder',
            uses=test_executor_image_name,
            needs='segmenter',
            uses_with={'name': 'textencoder'}
        )
        .add(
            name='textstorage',
            uses=test_executor_image_name,
            needs='textencoder',
            uses_with={'name': 'textstorage'},
        )
        .add(
            name='imageencoder',
            uses=test_executor_image_name,
            needs='segmenter',
            uses_with={'name': 'imageencoder'},
        )
        .add(
            name='imagestorage',
            uses=test_executor_image_name,
            needs='imageencoder',
            uses_with={'name': 'imageencoder'},
        )
    )
    return index_flow


def test_deploy(k8s_index_flow: Flow):
    with KindClusterWithTestClient() as test_client:

        k8s_index_flow.deploy('k8s')

        pods = test_client.list_pods('index-flow')
        for pod in pods:
            print(pod.status)


def test_deploy_with_l(kind_cluster, executor_image, k8s_index_flow: Flow):
    test_executor_image_name = executor_image.tags[0]

    kind_cluster.load_docker_image(test_executor_image_name)

    k8s_index_flow.deploy('k8s')

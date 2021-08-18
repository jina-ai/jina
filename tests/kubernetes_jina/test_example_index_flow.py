import pytest
from typing import Generator, Dict, List
from http import HTTPStatus

import requests

from jina import Flow, Document, DocumentArray
import pykube


@pytest.fixture()
def products() -> List[Dict]:
    data = [
        {
            "name": f"Gucci Handbag {i+100}",
            "description": "Black handbag from Gucci with golden decorations.",
            "uri": "https://media.gucci.com/style/"
                   "DarkGray_Center_0_0_1200x1200/"
                   "1538487908/474575_DTD1T_1000_001_100_0023_Light-GG-Marmont-matelass-mini-bag.jpg",
        }
        for i in range(10)
    ]
    return data


@pytest.fixture()
def k8s_index_flow(executor_image) -> Flow:
    # TODO: Fix: implicitly pulls Gateway and JoinAll executor from remote should be avoided
    index_flow = (
        Flow(name='index-flow', port_expose=8080, protocol='http')
        .add(
            name='segmenter',
            uses=executor_image,
            uses_with={'name': 'segmenter'}
        ).add(
            name='textencoder',
            uses=executor_image,
            needs='segmenter',
            uses_with={'name': 'textencoder'}
        )
        .add(
            name='textstorage',
            uses=executor_image,
            needs='textencoder',
            uses_with={'name': 'textstorage'},
        )
        .add(
            name='imageencoder',
            uses=executor_image,
            needs='segmenter',
            uses_with={'name': 'imageencoder'},
        )
        .add(
            name='imagestorage',
            uses=executor_image,
            needs='imageencoder',
            uses_with={'name': 'imagestorage'},
        )
    ).needs_all()
    return index_flow


def test_deploy(k8s_cluster, executor_image, k8s_index_flow: Flow, products: List[Dict]):
    expected_running_pods = 7
    valid_phases = ['Pending', 'ContainerCreating', 'Running']
    # image pull anyways must be Never or IfNotPresent otherwise kubernetes will try to pull the image anyway
    k8s_cluster.load_docker_image(executor_image)

    k8s_index_flow.deploy('k8s')

    api = pykube.HTTPClient(pykube.KubeConfig.from_file())
    running_pods = []
    # TODO: Is there a better way to wait for pods to reach Running phase?
    waiting = True
    while waiting:
        for pod in list(pykube.Pod.objects(api, namespace='index-flow')):
            assert pod.obj['status']['phase'] in valid_phases, f'Pod {pod.name} is in invalid phase' \
                                                               f' {pod.obj["status"]["phase"]}.'
            if pod.obj['status']['phase'] == 'Running' and pod.name not in running_pods:
                running_pods.append(pod.name)
        if len(running_pods) == expected_running_pods:
            waiting = False

    expected_traversed_executors = ['segmenter', 'imageencoder', 'textencoder', 'imagestorage', 'textstorage']

    # TODO: Fix Connection Refused Error (appears inconsistently)
    with k8s_cluster.port_forward('service/gateway', 8080, '-n', 'index-flow', local_port=8080) as port:

        resp = requests.post(f'http://localhost:8080/index', json={'data': products})
        assert resp.status_code == HTTPStatus.OK
        docs = resp.json()['data']['docs']
        for doc in docs:
            assert sorted(list(doc['tags']['traversed-executors'])) == sorted(expected_traversed_executors)

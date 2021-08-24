import time

import pytest
from typing import Dict, List
from http import HTTPStatus

import requests

from jina import Flow


@pytest.fixture()
def products() -> List[Dict]:
    data = [
        {
            "name": f"Gucci Handbag {i+1}",
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
        Flow(name='index-flow', port_expose=8080, infrastructure='K8S', protocol='http')
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
    )
    # ).needs_all()
    return index_flow


@pytest.mark.timeout(360)
def test_deploy(k8s_cluster, executor_image, k8s_index_flow: Flow, products: List[Dict], logger):
    expected_running_pods = 6  # TODO: set to 7 when joiner is finished

    # image pull anyways must be Never or IfNotPresent otherwise kubernetes will try to pull the image anyway
    logger.debug(f'Loading docker image {executor_image} into kind cluster...')
    k8s_cluster.needs_docker_image(executor_image)
    logger.debug(f'Done loading docker image {executor_image} into kind cluster...')

    logger.debug(f'Starting flow on kind cluster...')
    k8s_index_flow.start()
    logger.debug(f'Done starting flow on kind cluster...')

    # TODO: Is there a better way to wait for pods to reach Running phase?
    logger.debug(f'Starting to wait for pods in kind cluster to reach "RUNNING" state...')
    waiting = True
    while waiting:
        num_running_pods = len(k8s_cluster.list_ready_pods('index-flow'))
        if num_running_pods == expected_running_pods:
            waiting = False
        time.sleep(3)
        logger.debug(f'Still waiting for pods to reach running state '
                     f'(Current Status: {num_running_pods}/{expected_running_pods}).')

    expected_traversed_executors = ['segmenter', 'imageencoder', 'textencoder', 'imagestorage', 'textstorage']

    logger.debug(f'Starting port-forwarding to gateway service...')
    with k8s_cluster.port_forward('service/gateway', 8080, 8080, 'index-flow') as _:
        logger.debug(f'Port-forward running...')

        resp = requests.post(f'http://localhost:8080/index', json={'data': products})
        logger.debug(resp.status_code)

    assert resp.status_code == HTTPStatus.OK
    docs = resp.json()['data']['docs']
    for doc in docs:
        assert sorted(list(doc['tags']['traversed-executors'])) == sorted(expected_traversed_executors)

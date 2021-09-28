from typing import Dict

KIND = 'ConfigMap'
API_VERSION = 'v1'


def create(client: 'ApiClient', namespace: str, metadata: Dict, data: Dict) -> int:
    """Create k8s configmap for namespace given a client instance.

    :param client: k8s client instance.
    :param namespace: the namespace of the config map.
    :param metadata: config map metadata, should follow the :class:`V1ObjectMeta` schema.
    :param data: the environment variables represented as dict.
    :return status_code: the status code of the http request.
    """
    from kubernetes.client.api import core_v1_api

    api = core_v1_api.CoreV1Api(client)
    body = {
        'kind': KIND,
        'apiVersion': API_VERSION,
        'metadata': metadata,
        'data': {},
    }
    for key, value in data.items():
        body['data'][key] = value

    _, status_code, _ = api.create_namespaced_config_map(body=body, namespace=namespace)
    return status_code


def delete(client: 'ApiClient', namespace: str, name: str) -> int:
    """Create k8s configmap for namespace given a client instance.

    :param client: k8s client instance.
    :param namespace: the namespace of the config map.
    :param name: config map name.
    :return status_code: the status code of the http request.
    """
    from kubernetes.client.api import core_v1_api

    api = core_v1_api.CoreV1Api(client)
    _, status_code, _ = api.delete_namespaced_config_map(
        name=name, body={}, namespace=namespace
    )
    return status_code


def patch(client: 'ApiClient', namespace: str, name: str, data: Dict) -> int:
    """Patch k8s configmap for namespace given a client instance.

    :param client: k8s client instance.
    :param namespace: the namespace of the config map.
    :param name: config map name.
    :param data: the environment variables represented as dict. The key of the dict should
        exist in current config map.
    :return status_code: the status code of the http request.
    """
    from kubernetes.client.api import core_v1_api

    api = core_v1_api.CoreV1Api(client)
    config_map, status_code, _ = api.read_namespaced_config_map(
        name=name, namespace=namespace
    )
    if status_code < 200 or status_code > 299:
        raise Exception(
            f'failed to read configmap given name {name} within namespace {namespace}.'
        )  # TODO: exception
    body = config_map.to_dict()
    for key, value in data.items():
        if key in body['data']:
            body['data'][key] = value
    _, status_code, _ = api.patch_namespaced_config_map(
        name=name, namespace=namespace, body=body
    )
    return status_code

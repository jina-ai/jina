from typing import Dict, List

KIND = 'ConfigMap'
API_VERSION = 'v1'


def _create(client: 'ApiClient', metadata: Dict, data: Dict) -> int:
    """Create k8s configmap for namespace given a client instance.

    :param client: k8s client instance.
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

    _, status_code, _ = api.create_namespaced_config_map(
        body=body, namespace=metadata['namespace']
    )

    return status_code


def _patch(client: 'ApiClient', metadata: Dict, data: Dict) -> int:
    """Patch k8s configmap for namespace given a client instance.

    :param client: k8s client instance.
    :param metadata: config map metadata, should follow the :class:`V1ObjectMeta` schema.
    :param data: the environment variables represented as dict. The key of the dict should
        exist in current config map.
    :return status_code: the status code of the http request.
    """
    from kubernetes.client.api import core_v1_api

    api = core_v1_api.CoreV1Api(client)

    name = metadata['name']
    namespace = metadata['namespace']

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


def create_or_patch(client: 'ApiClient', metadata: Dict, data: Dict) -> int:
    """Check if the config map exist, if so patch, otherwise create.

    :param client: k8s client instance.
    :param metadata: config map metadata, should follow the :class:`V1ObjectMeta` schema.
    :param data: the environment variables represented as dict.
    :return status_code: the status code of the http request.
    """
    from kubernetes.client.api import core_v1_api

    api = core_v1_api.CoreV1Api(client)

    name = metadata.get('name')
    namespace = metadata.get('namespace')
    if not name or not namespace:
        raise ValueError(
            'Please assign a name and namespace to the metadata, got None.'
        )

    resp = api.list_namespaced_config_map(namespace)

    if name in resp.items():
        status_code = _patch(client=client, metadata=metadata, data=data)
    else:
        status_code = _create(client=client, metadata=metadata, data=data)
    return status_code


def attach(names: List[str]) -> List['V1EnvFromSource']:
    """Attached configmaps by names.

    :param names: List of configmaps to be attached to pod.

    ..note::
        It should be feed into :class:`KubernetesPodOperator`
        with argument `env_from`.
    """
    from kubernetes.client import models

    configmaps = []
    for name in names:
        configmaps.append(
            models.V1EnvFromSource(
                config_map_ref=models.V1ConfigMapEnvSource(name=name)
            )
        )
    return configmaps

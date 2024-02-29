import json
import math
import os
import warnings
from typing import Dict, List, Optional, Union

from jina.orchestrate.deployments.config.k8slib import kubernetes_tools
from jina.serve.networking import GrpcConnectionPool

PERIOD_SECONDS = 5


def get_template_yamls(
    name: str,
    namespace: str,
    image_name: str,
    container_cmd: str,
    container_args: str,
    replicas: int,
    pull_policy: str,
    jina_deployment_name: str,
    pod_type: str,
    shard_id: Optional[int] = None,
    env: Optional[Dict] = None,
    env_from_secret: Optional[Dict] = None,
    image_pull_secrets: Optional[List] = None,
    gpus: Optional[Union[int, str]] = None,
    image_name_uses_before: Optional[str] = None,
    image_name_uses_after: Optional[str] = None,
    container_cmd_uses_before: Optional[str] = None,
    container_cmd_uses_after: Optional[str] = None,
    container_args_uses_before: Optional[str] = None,
    container_args_uses_after: Optional[str] = None,
    monitoring: bool = False,
    protocol: Optional[Union[str, List[str]]] = None,
    volumes: Optional[List[str]] = None,
    timeout_ready: int = 600000,
) -> List[Dict]:
    """Get the yaml description of a service on Kubernetes

    :param name: name of the service and deployment
    :param namespace: k8s namespace of the service and deployment
    :param image_name: image for the k8s deployment
    :param container_cmd: command executed on the k8s pods
    :param container_args: arguments used for the k8s pod
    :param replicas: number of replicas
    :param pull_policy: pull policy used for fetching the Docker images from the registry.
    :param jina_deployment_name: Name of the Jina Deployment this deployment belongs to
    :param pod_type: type os this pod, can be gateway/head/worker
    :param shard_id: id of this shard, None if shards=1 or this is gateway/head
    :param env: environment variables to be passed into configmap.
    :param env_from_secret: environment variables from secret to be passed to this pod
    :param image_pull_secrets: list of secrets to be added uder ImagePullSecrets
    :param gpus: number of gpus to use, for k8s requires you pass an int number, refers to the number of requested gpus.
    :param image_name_uses_before: image for uses_before container in the k8s deployment
    :param image_name_uses_after: image for uses_after container in the k8s deployment
    :param container_cmd_uses_before: command executed in the uses_before container on the k8s pods
    :param container_cmd_uses_after: command executed in the uses_after container on the k8s pods
    :param container_args_uses_before: arguments used for uses_before container on the k8s pod
    :param container_args_uses_after: arguments used for uses_after container on the k8s pod
    :param monitoring: enable monitoring on the deployment
    :param protocol: In case of being a Gateway, the protocol or protocols list used to expose its server
    :param volumes: If volumes are passed to Executors, Jina will create a StatefulSet instead of Deployment and include the first volume in the volume mounts
    :param timeout_ready: The timeout in milliseconds of a Pod waits for the runtime to be ready. This parameter will be
        reflected in Kubernetes in the startup configuration where the failureThreshold will be calculated depending on
        timeout_ready. Value -1 is not supported for kubernetes
    :return: Return a dictionary with all the yaml configuration needed for a deployment
    """
    # we can always assume the ports are the same for all executors since they run on different k8s pods
    # port expose can be defined by the user
    port = (
        [GrpcConnectionPool.K8S_PORT + i for i in range(len(protocol))]
        if isinstance(protocol, list)
        else GrpcConnectionPool.K8S_PORT
    )  # TODO: This cannot happen
    port_monitoring = GrpcConnectionPool.K8S_PORT_MONITORING

    # we cast port to list of ports and protocol to list of protocols
    if not isinstance(port, list):
        ports = [port]
    else:
        ports = port
    if not isinstance(protocol, list):
        protocols = [protocol]
    else:
        protocols = protocol

    if timeout_ready == -1:
        warnings.warn(
            'timeout_ready=-1 is not supported, setting timeout_ready to 10 minutes'
        )
        timeout_ready = 600000
    failure_threshold = max(math.ceil((timeout_ready / 1000) / PERIOD_SECONDS), 3)

    template_params = {
        'name': name,
        'namespace': namespace,
        'image': image_name,
        'replicas': replicas,
        'command': container_cmd,
        'args': container_args,
        'port': ports[0],
        'port_uses_before': GrpcConnectionPool.K8S_PORT_USES_BEFORE,
        'port_uses_after': GrpcConnectionPool.K8S_PORT_USES_AFTER,
        'args_uses_before': container_args_uses_before,
        'args_uses_after': container_args_uses_after,
        'command_uses_before': container_cmd_uses_before,
        'command_uses_after': container_cmd_uses_after,
        'image_uses_before': image_name_uses_before,
        'image_uses_after': image_name_uses_after,
        'pull_policy': pull_policy,
        'jina_deployment_name': jina_deployment_name,
        'shard_id': f'\"{shard_id}\"' if shard_id is not None else '\"\"',
        'pod_type': pod_type,
        'env_from_secret': env_from_secret,
        'image_pull_secrets': image_pull_secrets,
        'protocol': str(protocols[0]).lower() if protocols[0] is not None else '',
        'volume_path': volumes[0] if volumes is not None else None,
        'period_seconds': PERIOD_SECONDS,
        'failure_threshold': failure_threshold,
    }

    if gpus and gpus != 'all':
        template_params['device_plugins'] = {'nvidia.com/gpu': gpus}

    template_name = 'deployment-executor' if name != 'gateway' else 'deployment-gateway'

    template_params['ports-section'] = ''.join(
        [f'\n            - containerPort: {_p}' for _p in ports]
    )

    if volumes:
        template_name = 'statefulset-executor'
        template_params['accessModes'] = json.loads(
            os.environ.get('JINA_K8S_ACCESS_MODES', '["ReadWriteOnce"]')
        )
        template_params['storageClassName'] = os.environ.get(
            'JINA_K8S_STORAGE_CLASS_NAME', 'standard'
        )
        template_params['storageCapacity'] = os.environ.get(
            'JINA_K8S_STORAGE_CAPACITY', '10G'
        )
    elif image_name_uses_before and image_name_uses_after:
        template_name = 'deployment-uses-before-after'
    elif image_name_uses_before:
        template_name = 'deployment-uses-before'
    elif image_name_uses_after:
        template_name = 'deployment-uses-after'

    if monitoring:
        service_yaml = kubernetes_tools.get_yaml(
            'service_monitoring',
            {
                'name': name,
                'target': name,
                'namespace': namespace,
                'port': ports[0],
                'type': 'ClusterIP',
                'port_monitoring': port_monitoring,
            },
        )

        service_monitor_yaml = kubernetes_tools.get_yaml(
            'service_monitor',
            {
                'name': name,
                'target': name,
                'namespace': namespace,
            },
        )
    else:
        service_yaml = kubernetes_tools.get_yaml(
            'service',
            {
                'name': name,
                'target': name,
                'namespace': namespace,
                'port': ports[0],
                'type': 'ClusterIP',
            },
        )
        service_monitor_yaml = None

    extra_services = [
        kubernetes_tools.get_yaml(
            'service',
            {
                'name': f'{name}-{i}-{protocol}'.lower(),
                'target': name,
                'namespace': namespace,
                'port': port,
                'type': 'ClusterIP',
            },
        )
        for i, (port, protocol) in enumerate(zip(ports[1:], protocols[1:]), start=1)
    ]

    template_yaml = kubernetes_tools.get_yaml(template_name, template_params)

    if 'JINA_LOG_LEVEL' in os.environ:
        env = env or {}
        env['JINA_LOG_LEVEL'] = os.environ['JINA_LOG_LEVEL']

    yamls = [
        kubernetes_tools.get_yaml(
            'configmap',
            {
                'name': name,
                'namespace': namespace,
                'data': env,
            },
        ),
        service_yaml,
        *extra_services,
        template_yaml,
    ]

    if service_monitor_yaml:
        yamls.append(service_monitor_yaml)

    return yamls

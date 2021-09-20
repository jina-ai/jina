import json
from argparse import Namespace
from typing import Dict, Optional, Tuple

from jina.hubble.helper import parse_hub_uri
from jina.hubble.hubio import HubIO
from jina.logging.logger import JinaLogger
from jina.peapods.pods.k8slib import kubernetes_tools


def to_dns_name(name: str) -> str:
    """Converts the pod name to a dns compatible name.

    :param name: name of the pod
    :return: dns compatible name
    """
    return name.replace('/', '-').replace('_', '-').lower()


def deploy_service(
    name: str,
    namespace: str,
    image_name: str,
    container_cmd: str,
    container_args: str,
    logger: JinaLogger,
    replicas: int,
    pull_policy: str,
    init_container: Dict = None,
    custom_resource_dir: Optional[str] = None,
) -> str:
    """Deploy service on Kubernetes.

    :param name: name of the service and deployment
    :param namespace: k8s namespace of the service and deployment
    :param image_name: image for the k8s deployment
    :param container_cmd: command executed on the k8s pods
    :param container_args: arguments used for the k8s pod
    :param logger: used logger
    :param replicas: number of replicas
    :param pull_policy: pull policy used for fetching the Docker images from the registry.
    :param init_container: additional arguments used for the init container
    :param custom_resource_dir: Path to a folder containing the kubernetes yml template files.
        Defaults to the standard location jina.resources if not specified.
    :return: dns name of the created service
    """

    # small hack - we can always assume the ports are the same for all executors since they run on different k8s pods
    port_expose = 8080
    port_in = 8081
    port_out = 8082
    port_ctrl = 8083

    logger.info(
        f'🔋\tCreate Service for "{name}" with image "{name}" pulling from "{image_name}"'
    )
    kubernetes_tools.create(
        'service',
        {
            'name': name,
            'target': name,
            'namespace': namespace,
            'port_expose': port_expose,
            'port_in': port_in,
            'port_out': port_out,
            'port_ctrl': port_ctrl,
            'type': 'ClusterIP',
        },
        logger=logger,
        custom_resource_dir=custom_resource_dir,
    )

    logger.info(
        f'🐳\tCreate Deployment for "{image_name}" with replicas {replicas} and init_container {init_container is not None}'
    )

    if init_container:
        template_name = 'deployment-init'
    else:
        template_name = 'deployment'
        init_container = {}
    kubernetes_tools.create(
        template_name,
        {
            'name': name,
            'namespace': namespace,
            'image': image_name,
            'replicas': replicas,
            'command': container_cmd,
            'args': container_args,
            'port_expose': port_expose,
            'port_in': port_in,
            'port_out': port_out,
            'port_ctrl': port_ctrl,
            'pull_policy': pull_policy,
            **init_container,
        },
        logger=logger,
        custom_resource_dir=custom_resource_dir,
    )
    return f'{name}.{namespace}.svc'


def get_cli_params(arguments: Namespace, skip_list: Tuple[str] = ()) -> str:
    """Get cli parameters based on the arguments.

    :param arguments: arguments where the cli parameters are generated from
    :param skip_list: list of arguments which should be ignored

    :return: string which contains all cli parameters
    """
    arguments.host = '0.0.0.0'
    skip_attributes = [
        'uses',  # set manually
        'uses_with',  # set manually
        'runtime_cls',  # set manually
        'workspace',
        'log_config',
        'dynamic_routing',
        'hosts_in_connect',
        'polling_type',
        'k8s_namespace',
        'uses_after',
        'uses_before',
        'replicas',
        'polling',
        'port_in',
        'port_out',
        'port_ctrl',
        'port_expose',
        'k8s_init_container_command',
        'k8s_uses_init',
        'k8s_mount_path',
    ] + list(skip_list)
    arg_list = [
        [attribute, attribute.replace('_', '-'), value]
        for attribute, value in arguments.__dict__.items()
    ]
    cli_args = []
    for attribute, cli_attribute, value in arg_list:
        if attribute in skip_attributes:
            continue
        if type(value) == bool and value:
            cli_args.append(f'"--{cli_attribute}"')
        else:
            if value:
                value = str(value)
                value = value.replace('\'', '').replace('"', '\\"')
                cli_args.append(f'"--{cli_attribute}", "{value}"')

    cli_args.append('"--port-expose", "8080"')
    cli_args.append('"--port-in", "8081"')
    cli_args.append('"--port-out", "8082"')
    cli_args.append('"--port-ctrl", "8083"')

    cli_string = ', '.join(cli_args)
    return cli_string


def get_image_name(uses: str) -> str:
    """The image can be provided in different formats by the user.
    This function converts it to an image name which can be understood by k8s.
    It uses the Hub api to get the image name and the latest tag on Docker Hub.
    :param uses: image name

    :return: normalized image name
    """
    try:
        scheme, name, tag, secret = parse_hub_uri(uses)
        meta_data = HubIO.fetch_meta(name)
        image_name = meta_data.image_name
        return image_name
    except Exception:
        return uses.replace('docker://', '')


def dictionary_to_cli_param(dictionary) -> str:
    """Convert the dictionary into a string to pass it as argument in k8s.
    :param dictionary: dictionary which has to be passed as argument in k8s.

    :return: string representation of the dictionary
    """
    return json.dumps(dictionary).replace('"', '\\"') if dictionary else ""


def get_init_container_args(pod) -> Optional[Dict]:
    """Return the init container arguments for the k8s pod.

    :param pod: pod where the init container is used.
    :return: dictionary of init container arguments
    """
    if pod.args.k8s_uses_init:
        init_container = {
            'init-name': 'init',
            'init-image': pod.args.k8s_uses_init,
            'init-command': f'{pod.args.k8s_init_container_command}',
            'mount-path': pod.args.k8s_mount_path,
        }
    else:
        init_container = None
    return init_container

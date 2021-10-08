import json
import os
import tempfile
from typing import Dict, Optional, Generator

from .client import K8sClients
from ....importer import ImportExtensions
from ....logging.logger import JinaLogger
from ....logging.predefined import default_logger

cur_dir = os.path.dirname(__file__)
DEFAULT_RESOURCE_DIR = os.path.join(
    cur_dir, '..', '..', '..', 'resources', 'k8s', 'template'
)


_k8s_clients = K8sClients()


def create(
    template: str,
    params: Dict,
    logger: JinaLogger = default_logger,
    custom_resource_dir: Optional[str] = None,
):
    """Create a resource on Kubernetes based on the `template`. It fills the `template` using the `params`.

    :param template: path to the template file.
    :param custom_resource_dir: Path to a folder containing the kubernetes yml template files.
        Defaults to the standard location jina.resources if not specified.
    :param logger: logger to use. Defaults to the default logger.
    :param params: dictionary for replacing the placeholders (keys) with the actual values.
    """

    from kubernetes.utils import FailToCreateError
    from kubernetes import utils

    yaml = _get_yaml(template, params, custom_resource_dir)
    fd, path = tempfile.mkstemp()
    try:
        with os.fdopen(fd, 'w') as tmp:
            tmp.write(yaml)
        try:
            utils.create_from_yaml(_k8s_clients.k8s_client, path)
        except FailToCreateError as e:
            for api_exception in e.api_exceptions:
                if api_exception.status == 409:
                    # The exception's body is the error response from the
                    # Kubernetes apiserver, it looks like:
                    # {..."message": "<resource> <name> already exists"...}
                    resp = json.loads(api_exception.body)
                    logger.info(f'🔁\t{resp["message"]}')
                else:
                    raise e
        except Exception as e2:
            raise e2
    finally:
        os.remove(path)


def _get_yaml(template: str, params: Dict, custom_resource_dir: Optional[str] = None):
    if custom_resource_dir:
        path = os.path.join(custom_resource_dir, f'{template}.yml')
    else:
        path = os.path.join(DEFAULT_RESOURCE_DIR, f'{template}.yml')
    with open(path) as f:
        content = f.read()
        for k, v in params.items():
            content = content.replace(f'{{{k}}}', str(v))
    return content


def _get_gateway_pod_name(namespace):
    gateway_pod = _k8s_clients.core_v1.list_namespaced_pod(
        namespace=namespace, label_selector='app=gateway'
    )
    return gateway_pod.items[0].metadata.name


def get_port_forward_contextmanager(
    namespace: str,
    port_expose: int,
    config_path: str = None,
) -> Generator[None, None, None]:
    """Forward local requests to the gateway which is running in the Kubernetes cluster.
    :param namespace: namespace of the gateway
    :param port_expose: exposed port of the gateway
    :param config_path: path to the Kubernetes config file
    :return: context manager which sets up and terminates the port-forward
    """
    with ImportExtensions(
        required=True,
        help_text='sending requests to the Kubernetes cluster requires to install the portforward package, '
        'please do `pip install jina[portforward]`',
    ):
        import portforward

    gateway_pod_name = _get_gateway_pod_name(namespace)
    if config_path is None and 'KUBECONFIG' in os.environ:
        config_path = os.environ['KUBECONFIG']
    return portforward.forward(
        namespace, gateway_pod_name, port_expose, port_expose, config_path
    )

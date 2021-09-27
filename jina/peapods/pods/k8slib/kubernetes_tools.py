import json
import os
import tempfile
from time import time, sleep
from typing import Dict, Optional

import portforward

from jina.logging.logger import JinaLogger
from jina.logging.predefined import default_logger

cur_dir = os.path.dirname(__file__)
DEFAULT_RESOURCE_DIR = os.path.join(
    cur_dir, '..', '..', '..', 'resources', 'k8s', 'template'
)

if False:
    from contextlib import GeneratorContextManager


class K8SClients:
    """
    The Kubernetes api is wrapped into a class to have a lazy reading of the cluster configuration.

    """

    def __init__(self):
        self.__k8s_client = None
        self.__v1 = None
        self.__beta = None
        self.__networking_v1_beta1_api = None

    def __instantiate(self):
        # this import reads the `KUBECONFIG` env var. Lazy load to postpone the reading
        from kubernetes import config, client

        try:
            # try loading kube config from disk first
            config.load_kube_config()
        except config.config_exception.ConfigException:
            # if the config could not be read from disk, try loading in cluster config
            # this works if we are running inside k8s
            config.load_incluster_config()

        self.__k8s_client = client.ApiClient()
        self.__v1 = client.CoreV1Api(api_client=self.__k8s_client)
        self.__beta = client.ExtensionsV1beta1Api(api_client=self.__k8s_client)
        self.__networking_v1_beta1_api = client.NetworkingV1beta1Api(
            api_client=self.__k8s_client
        )

    @property
    def k8s_client(self):
        """Client for making requests to Kubernetes

        :return: k8s client
        """
        if self.__k8s_client is None:
            self.__instantiate()
        return self.__k8s_client

    @property
    def v1(self):
        """V1 client for core

        :return: v1 client
        """
        if self.__v1 is None:
            self.__instantiate()
        return self.__v1

    @property
    def beta(self):
        """Beta client for using beta features

        :return: beta client
        """
        if self.__beta is None:
            self.__instantiate()
        return self.__beta

    @property
    def networking_v1_beta1_api(self):
        """Networking client used for creating the ingress

        :return: networking client
        """
        if self.__networking_v1_beta1_api is None:
            self.__instantiate()
        return self.__networking_v1_beta1_api


__k8s_clients = K8SClients()


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
            utils.create_from_yaml(__k8s_clients.k8s_client, path)
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
    gateway_pod = __k8s_clients.v1.list_namespaced_pod(
        namespace=namespace, label_selector='app=gateway'
    )
    return gateway_pod.items[0].metadata.name


def get_port_forward_contextmanager(
    namespace: str,
    port_expose: int,
    timeout: int = 60,
    config_path: str = None,
) -> 'GeneratorContextManager':
    """Forward local requests to the gateway which is running in the Kubernetes cluster.
    :param namespace: namespace of the gateway
    :param port_expose: exposed port of the gateway
    :param timeout: time in seconds to wait for the gateway to start
    :param config_path: path to the Kubernetes config file

    :return: context manager which sets up and terminates the port-forward
    """
    _wait_for_gateway(namespace, timeout)
    gateway_pod_name = _get_gateway_pod_name(namespace)
    if config_path is None and 'KUBECONFIG' in os.environ:
        config_path = os.environ['KUBECONFIG']
    return portforward.forward(
        namespace, gateway_pod_name, port_expose, port_expose, config_path
    )


def _wait_for_gateway(namespace: str, timeout: int):
    start = time()
    while time() - start < timeout:
        try:
            pods = __k8s_clients.v1.list_namespaced_pod(namespace=namespace)
            statuses = [item.status.phase == 'Running' for item in pods.items]
            if len(statuses) > 1 and all(statuses):
                return
        except:
            pass
        sleep(1)
    raise Exception(f'Gateway did not start after {timeout} seconds.')

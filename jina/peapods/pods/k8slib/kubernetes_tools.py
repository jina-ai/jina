import os
import tempfile
import json
from typing import Dict, Optional

from jina.logging.logger import JinaLogger
from jina.logging.predefined import default_logger

cur_dir = os.path.dirname(__file__)
DEFAULT_RESOURCE_DIR = os.path.join(
    cur_dir, '..', '..', '..', 'resources', 'k8s', 'template'
)


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

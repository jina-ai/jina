import os
import tempfile
import json
from typing import Dict, Optional, Generator

from ....importer import ImportExtensions
from ....logging.logger import JinaLogger
from ....logging.predefined import default_logger

cur_dir = os.path.dirname(__file__)
DEFAULT_RESOURCE_DIR = os.path.join(
    cur_dir, '..', '..', '..', 'resources', 'k8s', 'template'
)


class K8sClients:
    """
    The Kubernetes api is wrapped into a class to have a lazy reading of the cluster configuration.

    """

    def __init__(self):
        self._k8s_client = None
        self._core_v1 = None
        self._apps_v1 = None
        self._beta = None
        self._networking_v1_beta1_api = None

    def _instantiate(self):
        # this import reads the `KUBECONFIG` env var. Lazy load to postpone the reading
        from kubernetes import config, client

        try:
            # try loading kube config from disk first
            config.load_kube_config()
        except config.config_exception.ConfigException:
            # if the config could not be read from disk, try loading in cluster config
            # this works if we are running inside k8s
            config.load_incluster_config()

        self._k8s_client = client.ApiClient()
        self._core_v1 = client.CoreV1Api(api_client=self._k8s_client)
        self._apps_v1 = client.AppsV1Api(api_client=self._k8s_client)
        self._beta = client.ExtensionsV1beta1Api(api_client=self._k8s_client)
        self._networking_v1_beta1_api = client.NetworkingV1beta1Api(
            api_client=self._k8s_client
        )

    @property
    def k8s_client(self):
        """Client for making requests to Kubernetes

        :return: k8s client
        """
        if self._k8s_client is None:
            self._instantiate()
        return self._k8s_client

    @property
    def core_v1(self):
        """V1 client for core

        :return: v1 client
        """
        if self._core_v1 is None:
            self._instantiate()
        return self._core_v1

    @property
    def apps_v1(self):
        """V1 client for core

        :return: v1 client
        """
        if self._apps_v1 is None:
            self._instantiate()
        return self._apps_v1

    @property
    def beta(self):
        """Beta client for using beta features

        :return: beta client
        """
        if self._beta is None:
            self._instantiate()
        return self._beta

    @property
    def networking_v1_beta1_api(self):
        """Networking client used for creating the ingress

        :return: networking client
        """
        if self._networking_v1_beta1_api is None:
            self._instantiate()
        return self._networking_v1_beta1_api


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

    if template == 'configmap':
        yaml = _patch_configmap_yaml(template, params)
    else:
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
                    logger.warning(f'🔁\t{resp["message"]}')
                else:
                    raise e
        except Exception as e2:
            raise e2
    finally:
        os.remove(path)


def replace(
    deployment_name: str,
    namespace_name: str,
    template: str,
    params: Dict,
    custom_resource_dir: Optional[str] = None,
):
    """Create a resource on Kubernetes based on the `template`. It fills the `template` using the `params`.

    :param deployment_name: The name of the deployment to replace
    :param namespace_name: The name of the namespace where the deployment exists
    :param template: path to the template file.
    :param custom_resource_dir: Path to a folder containing the kubernetes yml template files.
        Defaults to the standard location jina.resources if not specified.
    :param params: dictionary for replacing the placeholders (keys) with the actual values.
    """

    import yaml

    yaml_file_path = _get_yaml(template, params, custom_resource_dir)
    fd, path = tempfile.mkstemp()
    try:
        with os.fdopen(fd, 'w') as tmp:
            tmp.write(yaml_file_path)
        with open(os.path.abspath(path)) as f:
            yml_document_all = yaml.safe_load(f)
        _k8s_clients.apps_v1.replace_namespaced_deployment(
            deployment_name, namespace_name, yml_document_all
        )
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


def _patch_configmap_yaml(template: str, params: Dict):
    import yaml

    path = os.path.join(DEFAULT_RESOURCE_DIR, f'{template}.yml')

    with open(path) as f:
        config_map = yaml.safe_load(f)

    config_map['metadata']['name'] = params.get('name') + '-' + 'configmap'
    config_map['metadata']['namespace'] = params.get('namespace')
    if params.get('data'):
        for key, value in params['data'].items():
            config_map['data'][key] = value
    return json.dumps(config_map)


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
        help_text='Sending requests to the Kubernetes cluster requires to install the portforward package. '
        'Please do `pip install "jina[portforward]"`'
        'Also make sure golang is installed `https://golang.org/`',
    ):
        import portforward

    gateway_pod_name = _get_gateway_pod_name(namespace)
    if config_path is None and 'KUBECONFIG' in os.environ:
        config_path = os.environ['KUBECONFIG']
    return portforward.forward(
        namespace, gateway_pod_name, port_expose, port_expose, config_path
    )

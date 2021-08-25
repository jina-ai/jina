import os
import tempfile

cur_dir = os.path.dirname(__file__)


class ClientsSingelton:
    def __init__(self):
        self.__k8s_client = None
        self.__v1 = None
        self.__beta = None
        self.__networking_v1_beta1_api = None

    def __instantiate(self):
        # this import reads the `KUBECONFIG` env var. Lazy load to postpone the reading
        from kubernetes import config, client

        config.load_kube_config()
        self.__k8s_client = client.ApiClient()
        self.__v1 = client.CoreV1Api(api_client=self.__k8s_client)
        self.__beta = client.ExtensionsV1beta1Api(api_client=self.__k8s_client)
        self.__networking_v1_beta1_api = client.NetworkingV1beta1Api(
            api_client=self.__k8s_client
        )

    @property
    def k8s_client(self):
        if self.__k8s_client is None:
            self.__instantiate()
        return self.__k8s_client

    @property
    def v1(self):
        if self.__v1 is None:
            self.__instantiate()
        return self.__v1

    @property
    def beta(self):
        if self.__beta is None:
            self.__instantiate()
        return self.__beta

    @property
    def networking_v1_beta1_api(self):
        if self.__networking_v1_beta1_api is None:
            self.__instantiate()
        return self.__networking_v1_beta1_api


__clients_singelton = ClientsSingelton()


def create(template, params):
    from kubernetes.utils import FailToCreateError
    from kubernetes import utils

    yaml = get_yaml(template, params)
    fd, path = tempfile.mkstemp()
    try:
        with os.fdopen(fd, 'w') as tmp:
            tmp.write(yaml)
        try:
            utils.create_from_yaml(__clients_singelton.k8s_client, path)
        except FailToCreateError as e:
            if e.api_exceptions[0].status == 409:
                print('exists already')
            else:
                raise e
        except Exception as e2:
            raise e2
    finally:
        os.remove(path)


def get_yaml(template, params):
    path = os.path.join(cur_dir, 'template', f'{template}.yml')
    with open(path) as f:
        content = f.read()
        for k, v in params.items():
            content = content.replace(f'{{{k}}}', str(v))
    return content


def get_service_cluster_ip(service_name, namespace):
    resp = __clients_singelton.v1.read_namespaced_service(service_name, namespace)
    return resp.spec.cluster_ip

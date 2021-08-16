# Contains useful functions to create, inspect & delete a kubernetes cluster

import os
import subprocess
from typing import List

import docker
import kubernetes as k8s

from jina.logging.logger import JinaLogger

cur_dir = os.path.dirname(__file__)


class ClusterExistsException(RuntimeError):
    pass


class KubernetesTestClient(object):
    def __init__(self):
        k8s.config.load_kube_config()
        self._k8s_client = k8s.client.CoreV1Api()

    def list_pods(self, namespace: str) -> List:
        ret = self._k8s_client.list_namespaced_pod(namespace)
        return [pod for pod in ret.items]


class KindClusterWithTestClient:
    """
    Context manager for test require a kind kubernetes cluster.
    The cluster is connected to a local docker registry (which is also created if not present).
    Docker images which are pushed to `localhost:5000` are available from inside the cluster.
    E.g. docker push `localhost:5000/test-image:v.0` and
    `kubectl create deployment hello-server --image=localhost:5000/hello-app:1.0` works.

    See https://kind.sigs.k8s.io/docs/ for more information.
    """
    def __init__(self):
        self._log = JinaLogger(self.__class__.__name__)

    @staticmethod
    def _is_cluster_running():
        docker_client = docker.from_env()
        for container in docker_client.containers.list():
            if 'kind-control-plane' == container.name:
                return True
        return False

    @property
    def registry_base_address(self) -> str:
        return 'localhost:5000/'

    def __enter__(self) -> KubernetesTestClient:
        if not KindClusterWithTestClient._is_cluster_running():
            return_code = subprocess.call(os.path.join(cur_dir, 'start-kind-with-registry.sh'), shell=True)
            if return_code != 0:
                raise RuntimeError('Unable to start kind cluster!')
        else:
            self._log.error('Kind Cluster already running. Please remove before running the tests.')
            raise ClusterExistsException
        return KubernetesTestClient()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return_code = subprocess.call(os.path.join(cur_dir, 'delete-kind-cluster-with-registry.sh'), shell=True)
        if return_code != 0:
            raise RuntimeError('Unable to delete kind cluster!')

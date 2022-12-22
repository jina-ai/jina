import os
import random
import socket
import subprocess
import time
from contextlib import contextmanager
from subprocess import CalledProcessError
from typing import Generator

import docker
from docker import DockerClient
from pytest_kind import KindCluster

from jina.logging.logger import JinaLogger


class KindClusterWrapperV2:
    def __init__(self, kind_cluster: KindCluster, logger: JinaLogger) -> None:
        self._log: JinaLogger = logger
        self._cluster: KindCluster = kind_cluster
        self._cluster.ensure_kubectl()
        self._cluster.ensure_kind()
        os.environ['KUBECONFIG'] = str(self._cluster.kubeconfig_path)
        self._docker_client: DockerClient = docker.from_env()

    def create_namespace(self, namespace: str) -> bool:
        """Create a namespace in the kind cluster.

        Returns:
            bool: True if the namespace was created, False if it already exists.
        """
        self._log.info(f'Creating namespace {namespace}')
        try:
            self._cluster.kubectl('create', 'namespace', namespace)
            self._log.info(f'Namespace {namespace} created')
            return True
        except CalledProcessError as e:
            # TODO: How do you get the error message from CalledProcessError?
            self._log.info(f'Namespace {namespace} already exists')
            return False

    def delete_namespace(self, namespace: str) -> bool:
        """Delete a namespace in the kind cluster.

        Returns:
            bool: True if the namespace was deleted, False if it doesn't exist.
        """
        self._log.info(f'Deleting namespace {namespace}')
        try:
            self._cluster.kubectl('delete', 'namespace', namespace)
            self._log.info(f'Namespace {namespace} deleted')
            return True
        except CalledProcessError as e:
            # TODO: How do you get the error message from CalledProcessError?
            self._log.info(f"Namespace {namespace} doesn't exists")
            return False

    def deploy_from_dir(
        self, dir: str, namespace: str, timeout_seconds: int = 300
    ) -> None:
        """
        Deploy artifacts from a directory containing the k8s yaml files

        Args:
            dir: directory containing the k8s yaml files
            namespace: namespace to deploy to
            timeout_seconds: timeout in seconds. Default is 300 seconds.
        """
        self.create_namespace(namespace)
        artifacts: str = self._cluster.kubectl("apply", "-Rf", dir, '-n', namespace)

        # Wait for deployments to be available
        for artifact in artifacts.splitlines():
            if artifact.startswith('deployment'):
                deployment_name = artifact.split()[0]
                self._log.info(f'Awaiting deployment {deployment_name}')
                try:
                    self._cluster.kubectl(
                        'wait',
                        '--for=condition=available',
                        deployment_name,
                        f"--timeout={timeout_seconds}s",
                        '-n',
                        namespace,
                    )
                except CalledProcessError as e:
                    self._log.error(
                        f'Error while waiting for deployment {deployment_name}: {e}'
                    )
                    self.log_node_summaries(namespace)
                    self.log_pod_summaries(namespace)
                    self.log_failing_pods(namespace)
                    raise e
                self._log.info(f'Deployment {deployment_name} ready')

    def log_node_summaries(self, namespace: str) -> None:
        """Logs node summaries in a namespace."""
        self._log.info(self._cluster.kubectl('get', 'nodes', '-n', namespace))
        self._log.info(self._cluster.kubectl('describe', 'nodes', '-n', namespace))

    def log_pod_summaries(self, namespace: str) -> None:
        """Logs pod summaries in a namespace."""
        self._log.error(self._cluster.kubectl('get', 'pods', '-n', namespace))
        self._log.error(self._cluster.kubectl('describe', 'pods', '-n', namespace))

    def log_failing_pods(self, namespace: str) -> None:
        """Logs all pods that are not in a running state in a namespace."""
        self._log.info(f'Logging failing pods in {namespace}')
        pods = self._cluster.kubectl(
            'get', 'pods', '-n', namespace, '-o', 'jsonpath={.items[*].metadata.name}'
        )
        for pod in pods.split():
            if (
                self._cluster.kubectl(
                    'get',
                    'pods',
                    pod,
                    '-n',
                    namespace,
                    '-o',
                    'jsonpath={.status.phase}',
                )
                != 'Running'
            ):
                self._log.error(self._cluster.kubectl('logs', pod, '-n', namespace))

    async def async_deploy_from_dir(
        self, dir: str, namespace: str, timeout_seconds: int = 900
    ) -> None:
        """
        Deploy artifacts from a directory containing the k8s yaml files
        But wait for the deployments to be ready asynchronously

        Args:
            dir: directory containing the k8s yaml files
            namespace: namespace to deploy to
            timeout_seconds: timeout in seconds. Default is 900 seconds.
        """
        # TODO: Timeout should be shorter and should async sleep if failed
        raise NotImplementedError('Not implemented yet')

    def build_and_load_docker_image(self, dir: str, image_name: str, tag: str) -> str:
        """Build and load docker image.

        Args:
            dir: path to build directory
            image_name: name of the image
            tag: tag of the image
        Returns:
            str: image name with tag
        """
        self._log.info(f'Building docker image {image_name}:{tag}')
        self._docker_client.images.build(path=dir, tag=f'{image_name}:{tag}')
        self._log.info(f'Docker image {image_name}:{tag} built')
        self.load_docker_image(image_name, tag)
        return f'{image_name}:{tag}'

    def load_docker_image(self, image_name: str, tag: str) -> str:
        """Load docker image.

        Args:
            image_name: name of the image
            tag: tag of the image
        Returns:
            str: image name with tag
        """
        self._log.info(f'Loading docker image {image_name}:{tag}')
        self._cluster.load_docker_image(f'{image_name}:{tag}')
        self._log.info(f'Docker image {image_name}:{tag} loaded')
        return f'{image_name}:{tag}'

    def remove_docker_image(self, image_name: str, tag: str) -> None:
        """Remove docker image.

        Args:
            image_name: name of the image
            tag: tag of the image
        """
        self._log.info(f'Removing docker image {image_name}:{tag}')
        self._docker_client.images.remove(f'{image_name}:{tag}')
        self._log.info(f'Docker image {image_name}:{tag} removed')

    @contextmanager
    def port_forward(
        self,
        service_or_pod_name: str,
        namespace: str,
        svc_port: int,
        host_port: int = None,
        retries: int = 10,
    ) -> Generator[int, None, None]:
        """
        Run "kubectl port-forward" for the given service/pod.

        Args:
            service_or_pod_name: name of the service or pod
            namespace: namespace of the service or pod
            svc_port: service port to forward to
            host_port: host port to forward to. If None, a random port will be used.
            retries: number of retries to find a free port. Default is 10.
        """
        if host_port is None:
            host_port = random.randint(5000, 30000)

        proc = None

        for i in range(retries):
            if proc:
                proc.kill()
            proc = subprocess.Popen(
                [
                    str(self._cluster.kubectl_path),
                    "port-forward",
                    service_or_pod_name,
                    f"{host_port}:{svc_port}",
                    "-n",
                    namespace,
                ],
                env={"KUBECONFIG": str(self._cluster.kubeconfig_path)},
            )
            time.sleep(1)
            returncode = proc.poll()
            if returncode is not None:
                if i >= retries - 1:
                    raise Exception(
                        f"kubectl port-forward returned exit code {returncode}"
                    )
                else:
                    continue
            s = socket.socket()
            try:
                s.connect(("127.0.0.1", host_port))
            except:
                if i >= retries - 1:
                    raise
            finally:
                s.close()
        try:
            yield host_port
        finally:
            if proc:
                proc.kill()

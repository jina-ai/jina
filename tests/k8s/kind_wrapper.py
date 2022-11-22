import time
import random
import subprocess
import socket
import docker
import os
import json
from docker import DockerClient
from pytest_kind import KindCluster
from subprocess import CalledProcessError
from contextlib import contextmanager
from typing import Generator, List, Dict

from jina.logging.logger import JinaLogger


class KindClusterWrapper:
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

    def deploy_from_dir(self, dir: str, namespace: str, timeout_seconds: int = 300, validate: bool = True) -> None:
        """
        Deploy artifacts from a directory containing the k8s yaml files
        
        Args:
            dir: directory containing the k8s yaml files
            namespace: namespace to deploy to
            timeout_seconds: timeout in seconds. Default is 300 seconds.
            validate: whether or not to validate the deployed artifacts in kubectl apply
        """
        self.create_namespace(namespace)

        cmd: List[str] = ["apply", "-Rf", dir, '-n', namespace]
        if not validate:
            cmd.append('--validate=false')
        artifacts: str = self._cluster.kubectl(*cmd)

        # Wait for deployments to be available
        try:
            for artifact in artifacts.splitlines():
                if artifact.startswith('deployment'):
                    deployment_name = artifact.split()[0]
                    self._log.info(f'Awaiting deployment  of {deployment_name}')
                    self._cluster.kubectl('wait', '--for=condition=available', deployment_name, f"--timeout={timeout_seconds}s", '-n', namespace)
                    self._log.info(f'Deployment {deployment_name} ready')
                if artifact.startswith('statefulset'):
                    statefulset_name = artifact.split()[0]
                    for pod in self.get_pods_in_statefulset(namespace, statefulset_name.split('/')[1]):
                        self._log.info(f'Awaiting pod {pod} of {statefulset_name} to be ready')
                        self._cluster.kubectl('wait', '--for=condition=ready', 'pod', pod, f"--timeout={timeout_seconds}s", '-n', namespace)
                        self._log.info(f'Pod {pod} ready')

        except CalledProcessError as e:
            self._log.error(f'Error while waiting for {artifact}: {e}')
            self.log_node_summaries(namespace)
            self.log_pod_summaries(namespace)
            self.log_failing_pods(namespace)
            raise e
    
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
        pods = self._cluster.kubectl('get', 'pods', '-n', namespace, '-o', 'jsonpath={.items[*].metadata.name}')
        for pod in pods.split():
            if self._cluster.kubectl('get', 'pods', pod, '-n', namespace, '-o', 'jsonpath={.status.phase}') != 'Running':
                self._log.error(self._cluster.kubectl('logs', pod, '-n', namespace))

    async def async_deploy_from_dir(self, dir: str, namespace: str, timeout_seconds: int = 900) -> None:
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
    
    def build_and_load_docker_image(self, dir: str, image_repo_name: str, tag: str) -> str:
        """Build and load docker image.
        
        Args:
            dir: path to build directory
            image_repo_name (str): name of the image repository
            tag: tag of the image
        Returns:
            image_name (str): image name with (image_repo_name:tag)
        """
        image_name = f'{image_repo_name}:{tag}'
        self._log.info(f'Building docker image {image_name}')
        self._docker_client.images.build(path=dir, tag=f'{image_name}')
        self._log.info(f'Docker image {image_name} built')
        self.load_docker_image(image_repo_name, tag)
        return image_name
    
    def load_docker_image(self, image_repo_name: str, tag: str) -> str:
        """Load docker image.
        
        Args:
            image_repo_name (str): name of the image repository
            tag (str): tag of the image
        Returns:
            image_name (str): image name with (image_repo_name:tag)
        """
        image_name = f'{image_repo_name}:{tag}'
        self._log.info(f'Loading docker image {image_name}')
        self._cluster.load_docker_image(f'{image_name}')
        self._log.info(f'Docker image {image_name} loaded')
        return image_name
    
    def remove_docker_image(self, image_repo_name: str, tag: str) -> None:
        """Remove docker image.
        
        Args:
            image_repo_name: name of the image repository
            tag: tag of the image
        """
        image_name = f'{image_repo_name}:{tag}'
        self._log.info(f'Removing docker image {image_name}')
        self._docker_client.images.remove(f'{image_name}')
        self._log.info(f'Docker image {image_name} removed')

    def get_pod_name(self, namespace: str, label_selector: str) -> str:
        """Get pod name by label selector.
        
        Args:
            namespace: namespace of the pod
            label_selector: label selector of the pod
        Returns:
            pod_name: name of the pod
        """
        try:
            return self._cluster.kubectl('get', 'pods', '-n', namespace, '-l', label_selector, '-o', 'jsonpath={.items[0].metadata.name}').strip()
        except CalledProcessError as e:
            self._log.error(f'Error while getting pod name: {e}')
            self.log_node_summaries(namespace)
            self.log_pod_summaries(namespace)
            self.log_failing_pods(namespace)
            raise e

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

    def get_spec_template_labels(self, namespace: str, artifact_name: str) -> Dict[str, str]:
        """Get labels from spec.template.metadata.labels of a deployment or statefulset.
        
        Args:
            namespace: namespace of the deployment
            artifact_name: name of the deployment or statefulset
        Returns:
            labels: labels from spec.template.metadata.labels of a deployment
        """
        if not artifact_name.startswith('deployment') and not artifact_name.startswith('statefulset'):
            raise ValueError(f'Artifact must be start with either deployment or statefulset. Got {artifact_name}')

        labels = self._cluster.kubectl('get', artifact_name, '-n', namespace, '-o', 'jsonpath={.spec.template.metadata.labels}')
        return json.loads(labels)

    def get_pods_in_statefulset(self, namespace: str, statefulset_name: str) -> str:
        """Get pod name by label selector.
        
        Args:
            namespace: namespace of the pod
            statefulset_name: name of the statefulset
        Returns:
            pod_names: name of the pods
        """
        pod_labels = self.get_spec_template_labels(namespace, f'statefulset/{statefulset_name}')
        pod_labels = ','.join([f'{k}={v}' for k, v in pod_labels.items()])

        return self._cluster.kubectl('get', 'pods', '-n', namespace, '-l', pod_labels, '-o', 'jsonpath={.items[*].metadata.name}').split()

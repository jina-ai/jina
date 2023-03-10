import os
import socket

from jina import DocumentArray, Executor, requests


class TestExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from jina.logging.logger import JinaLogger

        self.logger = JinaLogger(self.__class__.__name__)
        self._name = self.runtime_args.name

    @requests(on='/debug')
    def debug(self, docs: DocumentArray, **kwargs):
        self.logger.debug(
            f'Received doc array in test-executor {self._name} with length {len(docs)}.'
        )
        key = 'traversed-executors'

        for doc in docs:
            if key not in doc.tags:
                doc.tags[key] = []
            traversed = list(doc.tags.get(key))
            traversed.append(self._name)
            doc.tags[key] = traversed
            doc.tags['parallel'] = self.runtime_args.replicas
            doc.tags['shards'] = self.runtime_args.shards
            doc.tags['shard_id'] = self.runtime_args.shard_id
            doc.tags['hostname'] = socket.gethostname()

    @requests(on='/env')
    def env(self, docs: DocumentArray, **kwargs):
        self.logger.debug(
            f'Received doc array in test-executor {self._name} with length {len(docs)}.'
        )

        for doc in docs:
            doc.tags['k1'] = os.environ.get('k1')
            doc.tags['k2'] = os.environ.get('k2')
            doc.tags['JINA_LOG_LEVEL'] = os.environ.get('JINA_LOG_LEVEL')
            doc.tags['env'] = {'k1': os.environ.get('k1'), 'k2': os.environ.get('k2')}
            doc.tags['SECRET_USERNAME'] = os.environ.get('SECRET_USERNAME')
            doc.tags['SECRET_PASSWORD'] = os.environ.get('SECRET_PASSWORD')

    @requests(on='/cuda')
    def cuda(self, docs: DocumentArray, **kwargs):
        self.logger.debug(
            f'Received doc array in test-executor {self._name} with length {len(docs)}.'
        )

        import kubernetes
        from kubernetes import client

        api_client = client.ApiClient()
        core_client = client.CoreV1Api(api_client=api_client)

        try:
            # try loading kube config from disk first
            kubernetes.config.load_kube_config()
        except kubernetes.config.config_exception.ConfigException:
            # if the config could not be read from disk, try loading in cluster config
            # this works if we are running inside k8s
            kubernetes.config.load_incluster_config()

        pods = core_client.list_namespaced_pod('test-gpu')  # List[V1Pod]
        pod_spec = pods[0].spec  # V1PodSpec
        pod_container = pod_spec.containers[0]  # V1Container
        pod_resources = pod_container.resources  # V1ResourceRequirements

        for doc in docs:
            doc.tags['resources']['limits'] = pod_resources.limits

    @requests(on='/workspace')
    def foo_workspace(self, docs: DocumentArray, **kwargs):
        import torch

        self.logger.debug(
            f'Received doc array in test-executor {self._name} with length {len(docs)}.'
        )
        self.logger.debug(f'Workspace {self.workspace}.')
        for doc in docs:
            doc.tags['workspace'] = self.workspace
            doc.embedding = torch.rand(1000)
            doc.tensor = torch.rand(1000)

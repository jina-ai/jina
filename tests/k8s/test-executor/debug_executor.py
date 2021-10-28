import os

from jina import Executor, requests, DocumentArray


class TestExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from jina.logging.logger import JinaLogger

        self.logger = JinaLogger(self.__class__.__name__)
        self._name = self.runtime_args.name

    @requests(on='/index')
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
            doc.tags['parallel'] = self.runtime_args.parallel
            doc.tags['shards'] = self.runtime_args.shards
            doc.tags['shard_id'] = self.runtime_args.shard_id
            doc.tags['pea_id'] = self.runtime_args.pea_id

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

    @requests(on='/cuda')
    def cuda(self, docs: DocumentArray, **kwargs):
        self.logger.debug(
            f'Received doc array in test-executor {self._name} with length {len(docs)}.'
        )

        from jina.peapods.pods.k8slib.kubernetes_client import K8sClients

        client = K8sClients().core_v1
        pods = client.list_namespaced_pod('test-gpu')  # List[V1Pod]
        pod_spec = pods[0].spec  # V1PodSpec
        pod_container = pod_spec.containers[0]  # V1Container
        pod_resources = pod_container.resources  # V1ResourceRequirements

        for doc in docs:
            doc.tags['resources']['limits'] = pod_resources.limits

    @requests(on='/search')
    def read_file(self, docs: DocumentArray, **kwargs):
        self.logger.debug(
            f'Received doc array in test-executor {self._name} with length {len(docs)}.'
        )
        key = 'file'
        file_path = '/shared/test_file.txt'

        with open(file_path, 'r') as text_file:
            lines = text_file.readlines()
        for doc in docs:
            doc.tags[key] = lines

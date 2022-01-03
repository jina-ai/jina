import copy
from argparse import Namespace
from typing import Dict, Union, List, Optional, Tuple

from .... import __default_executor__, __version__
from ....enums import PeaRoleType
from .. import BasePod


def _get_base_executor_version():
    import requests

    try:
        url = 'https://registry.hub.docker.com/v1/repositories/jinaai/jina/tags'
        tags = requests.get(url).json()
        name_set = {tag['name'] for tag in tags}
        if __version__ in name_set:
            return __version__
        else:
            return 'master'
    except:
        return 'master'


class DockerComposeConfig:
    """
    Class that implements the output of configuration files for docker-compose for a given Pod.
    """

    class _DockerComposeService:
        def __init__(
            self,
            name: str,
            version: str,
            pea_type: PeaRoleType,
            jina_pod_name: str,
            shard_id: Optional[int],
            common_args: Union['Namespace', Dict],
            service_args: Union['Namespace', Dict],
            pod_addresses: Optional[Dict[str, List[str]]] = None,
        ):
            self.name = name
            self.version = version
            self.pea_type = pea_type
            self.jina_pod_name = jina_pod_name
            self.shard_id = shard_id
            self.common_args = common_args
            self.service_args = service_args
            self.num_replicas = getattr(self.service_args, 'replicas', 1)
            self.pod_addresses = pod_addresses

        def get_gateway_config(
            self,
        ) -> Dict:
            import os

            test_pip = os.getenv('JINA_K8S_USE_TEST_PIP') is not None
            image_name = (
                'jinaai/jina:test-pip'
                if test_pip
                else f'jinaai/jina:{self.version}-py38-standard'
            )
            cargs = copy.copy(self.service_args)
            cargs.pods_addresses = self.pod_addresses
            from ....helper import ArgNamespace
            from ....parsers import set_gateway_parser

            non_defaults = ArgNamespace.get_non_defaults_args(
                cargs,
                set_gateway_parser(),
            )
            _args = ArgNamespace.kwargs2list(non_defaults)
            container_args = ['gateway'] + _args
            return {
                'image': image_name,
                'entrypoint': ['jina'],
                'command': container_args,
            }

        @staticmethod
        def _construct_runtime_container_args(cargs, uses_metas, uses_with, replica_id):
            import json
            from ....helper import ArgNamespace
            from ....parsers import set_pea_parser

            cargs.replica_id = replica_id

            non_defaults = ArgNamespace.get_non_defaults_args(
                cargs,
                set_pea_parser(),
                taboo={'uses_with', 'uses_metas'},
            )
            _args = ArgNamespace.kwargs2list(non_defaults)
            container_args = ['executor'] + _args
            if uses_metas is not None:
                container_args.extend(['--uses-metas', json.dumps(uses_metas)])
            if uses_with is not None:
                container_args.extend(['--uses-with', json.dumps(uses_with)])
            container_args.append('--native')
            return container_args

        def _get_image_name(self, uses: Optional[str]):
            import os

            test_pip = os.getenv('JINA_K8S_USE_TEST_PIP') is not None
            image_name = (
                'jinaai/jina:test-pip'
                if test_pip
                else f'jinaai/jina:{self.version}-py38-perf'
            )

            if uses is not None and uses != __default_executor__:
                image_name = kubernetes_deployment.get_image_name(uses)

            return image_name

        def _get_container_args(self, cargs, pea_type):
            uses_metas = cargs.uses_metas or {}
            if self.shard_id is not None:
                uses_metas['pea_id'] = self.shard_id
            uses_with = self.service_args.uses_with
            if cargs.uses != __default_executor__:
                cargs.uses = 'config.yml'
            return self._construct_runtime_container_args(
                cargs, uses_metas, uses_with, pea_type
            )

        def get_runtime_config(
            self,
        ) -> List[Dict]:
            # One Dict for replica
            replica_configs = []
            for replica_id in range(self.service_args.replicas):
                cargs = copy.copy(self.service_args)

                image_name = self._get_image_name(cargs.uses)
                container_args = self._get_container_args(
                    cargs, replica_id=replica_id, pea_type=self.pea_type
                )
                replica_configs.append(
                    {
                        'image': image_name,
                        'entrypoint': ['jina'],
                        'command': container_args,
                    }
                )
            return replica_configs

    def __init__(
        self,
        args: Union['Namespace', Dict],
        pod_addresses: Optional[Dict[str, List[str]]] = None,
    ):
        self.pod_addresses = pod_addresses
        self.head_deployment = None
        self.args = copy.copy(args)
        self.name = self.args.name

        self.services_args = self._get_services_args(self.args)

        if self.services_args['head_service'] is not None:
            self.head_service = self._DockerComposeService(
                name=self.services_args['head_service'].name,
                version=_get_base_executor_version(),
                shard_id=None,
                jina_pod_name=self.name,
                common_args=self.args,
                service_args=self.services_args['head_service'],
                pea_type=PeaRoleType.HEAD,
                pod_addresses=self.pod_addresses,
            )

        if self.services_args['uses_before_service'] is not None:
            self.uses_before_service = self._DockerComposeService(
                name=self.services_args['uses_before_service'].name,
                version=_get_base_executor_version(),
                shard_id=None,
                jina_pod_name=self.name,
                common_args=self.args,
                service_args=self.services_args['uses_before_service'],
                pea_type=PeaRoleType.WORKER,
                pod_addresses=None,
            )

        if self.services_args['uses_before_service'] is not None:
            self.uses_after_service = self._DockerComposeService(
                name=self.services_args['uses_after_service'].name,
                version=_get_base_executor_version(),
                shard_id=None,
                jina_pod_name=self.name,
                common_args=self.args,
                service_args=self.services_args['uses_after_service'],
                pea_type=PeaRoleType.WORKER,
                pod_addresses=None,
            )

        self.worker_services = []
        services_args = self.services_args['services']
        for i, args in enumerate(services_args):
            name = f'{self.name}-{i}' if len(services_args) > 1 else f'{self.name}'
            self.worker_services.append(
                self._DockerComposeService(
                    name=name,
                    version=_get_base_executor_version(),
                    shard_id=i,
                    common_args=self.args,
                    service_args=args,
                    pea_type=PeaRoleType.WORKER
                    if name != 'gateway'
                    else PeaRoleType.GATEWAY,
                    jina_pod_name=self.name,
                    pod_addresses=None,
                )
            )

    def _get_services_args(self, args):
        parsed_args = {
            'head_service': None,
            'uses_before_service': None,
            'uses_after_service': None,
            'services': [],
        }
        shards = getattr(args, 'shards', 1)
        uses_before = getattr(args, 'uses_before', None)
        uses_after = getattr(args, 'uses_after', None)

        if args.name != 'gateway':
            parsed_args['head_service'] = BasePod._copy_to_head_args(self.args)
            parsed_args['head_service'].port_in = 8081
            parsed_args['head_service'].uses = None
            parsed_args['head_service'].uses_metas = None
            parsed_args['head_service'].uses_with = None

            # if the k8s connection pool is disabled, the connection pool is managed manually
            import json

            connection_list = {}
            for i in range(shards):
                name = (
                    f'{kubernetes_deployment.to_dns_name(self.name)}-{i}'
                    if shards > 1
                    else f'{kubernetes_deployment.to_dns_name(self.name)}'
                )
                # TODO: Fix connection list
                # connection_list[
                #     str(i)
                # ] = f'{name}.{self.k8s_namespace}.svc:{K8sGrpcConnectionPool.K8S_PORT_IN}'

            parsed_args['head_service'].connection_list = json.dumps(connection_list)

        if uses_before:
            uses_before_cargs = copy.deepcopy(args)
            uses_before_cargs.shard_id = 0
            uses_before_cargs.replicas = 1
            uses_before_cargs.replica_id = -1
            uses_before_cargs.uses = args.uses_before
            uses_before_cargs.uses_before = None
            uses_before_cargs.uses_after = None
            uses_before_cargs.port_in = 8082
            uses_before_cargs.uses_before_address = None
            uses_before_cargs.uses_after_address = None
            uses_before_cargs.connection_list = None
            uses_before_cargs.pea_role = PeaRoleType.WORKER
            parsed_args['uses_before_service'] = uses_before_cargs
            parsed_args[
                'head_service'
            ].uses_before_address = f'127.0.0.1:{uses_before_cargs.port_in}'
        if uses_after:
            uses_after_cargs = copy.deepcopy(args)
            uses_after_cargs.shard_id = 0
            uses_after_cargs.replicas = 1
            uses_after_cargs.replica_id = -1
            uses_after_cargs.uses = args.uses_after
            uses_after_cargs.uses_before = None
            uses_after_cargs.uses_after = None
            uses_after_cargs.port_in = 8082
            uses_after_cargs.uses_before_address = None
            uses_after_cargs.uses_after_address = None
            uses_after_cargs.connection_list = None
            uses_after_cargs.pea_role = PeaRoleType.WORKER
            parsed_args['uses_after_service'] = uses_after_cargs
            parsed_args[
                'head_service'
            ].uses_after_address = f'127.0.0.1:{uses_after_cargs.port_in}'

        for i in range(shards):
            cargs = copy.deepcopy(args)
            cargs.shard_id = i
            cargs.uses_before = None
            cargs.uses_after = None
            cargs.k8s_connection_pool = False
            # cargs.port_in = K8sGrpcConnectionPool.K8S_PORT_IN
            if shards > 1:
                cargs.name = f'{cargs.name}-{i}'
            if args.name == 'gateway':
                cargs.pea_role = PeaRoleType.GATEWAY
            parsed_args['services'].append(cargs)

        return parsed_args

    def to_docker_compose_config(
        self,
    ) -> List[Tuple[str, Dict]]:
        """
        Return a list of dictionary configurations. One for each service in this Pod
            .. # noqa: DAR201
            .. # noqa: DAR101
        """
        if self.name == 'gateway':
            return [
                (
                    'gateway',
                    self.worker_services[0].get_gateway_config(),
                )
            ]
        else:
            services = [self.head_service]
            services.extend(self.worker_services)
            return [
                (
                    service.name,
                    service.get_runtime_config(),
                )
                for service in services
            ]

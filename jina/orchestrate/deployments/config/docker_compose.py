import copy
from argparse import Namespace
from typing import Dict, Union, List, Optional, Tuple

from jina import __default_executor__
from jina.excepts import NoContainerizedError
from jina.enums import PodRoleType
from jina.orchestrate.deployments.config.helper import (
    get_image_name,
    to_compatible_name,
    get_base_executor_version,
    construct_runtime_container_args,
    validate_uses,
)
from jina.orchestrate.deployments import BaseDeployment

port = 8081


class DockerComposeConfig:
    """
    Class that implements the output of configuration files for docker-compose for a given Deployment.
    """

    class _DockerComposeService:
        def __init__(
            self,
            name: str,
            version: str,
            pod_type: PodRoleType,
            jina_deployment_name: str,
            shard_id: Optional[int],
            common_args: Union['Namespace', Dict],
            service_args: Union['Namespace', Dict],
            deployments_addresses: Optional[Dict[str, List[str]]] = None,
        ):
            self.name = name
            self.compatible_name = to_compatible_name(self.name)
            self.version = version
            self.pod_type = pod_type
            self.jina_deployment_name = jina_deployment_name
            self.shard_id = shard_id
            self.common_args = common_args
            self.service_args = service_args
            self.num_replicas = getattr(self.service_args, 'replicas', 1)
            self.deployments_addresses = deployments_addresses

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
            cargs.deployments_addresses = self.deployments_addresses
            cargs.env = None
            from jina.helper import ArgNamespace
            from jina.parsers import set_gateway_parser

            taboo = {
                'uses_with',
                'uses_metas',
                'volumes',
                'uses_before',
                'uses_after',
                'workspace',
                'workspace_id',
                'upload_files',
                'noblock_on_start',
            }

            non_defaults = ArgNamespace.get_non_defaults_args(
                cargs, set_gateway_parser(), taboo=taboo
            )
            _args = ArgNamespace.kwargs2list(non_defaults)
            container_args = ['gateway'] + _args
            return {
                'image': image_name,
                'entrypoint': ['jina'],
                'command': container_args,
                'expose': [
                    f'{cargs.port}',
                ],
                'ports': [
                    f'{cargs.port}:{cargs.port}',
                ],
            }

        def _get_image_name(self, uses: Optional[str]):
            import os

            test_pip = os.getenv('JINA_K8S_USE_TEST_PIP') is not None
            image_name = (
                'jinaai/jina:test-pip'
                if test_pip
                else f'jinaai/jina:{self.version}-py38-perf'
            )

            if uses is not None and uses != __default_executor__:
                image_name = get_image_name(uses)

            return image_name

        def _get_container_args(self, cargs):
            uses_metas = cargs.uses_metas or {}
            uses_with = self.service_args.uses_with
            if cargs.uses != __default_executor__:
                cargs.uses = 'config.yml'
            return construct_runtime_container_args(
                cargs, uses_metas, uses_with, self.pod_type
            )

        def get_runtime_config(
            self,
        ) -> List[Dict]:
            # One Dict for replica
            replica_configs = []
            for i_rep in range(self.service_args.replicas):
                cargs = copy.copy(self.service_args)
                cargs.name = (
                    f'{cargs.name}/rep-{i_rep}'
                    if self.service_args.replicas > 1
                    else cargs.name
                )

                env = cargs.env
                image_name = self._get_image_name(cargs.uses)
                container_args = self._get_container_args(cargs)
                config = {
                    'image': image_name,
                    'entrypoint': ['jina'],
                    'command': container_args,
                }
                if env is not None:
                    config['environment'] = [f'{k}={v}' for k, v in env.items()]
                replica_configs.append(config)
            return replica_configs

    def __init__(
        self,
        args: Union['Namespace', Dict],
        deployments_addresses: Optional[Dict[str, List[str]]] = None,
    ):
        if not validate_uses(args.uses):
            raise NoContainerizedError(
                f'Executor "{args.uses}" is not valid to be used in docker-compose. '
                'You need to use a containerized Executor. You may check `jina hub --help` to see how Jina Hub can help you building containerized Executors.'
            )
        self.deployments_addresses = deployments_addresses
        self.head_service = None
        self.uses_before_service = None
        self.uses_after_service = None
        self.args = copy.copy(args)
        self.name = self.args.name

        self.services_args = self._get_services_args(self.args)

        if self.services_args['head_service'] is not None:
            self.head_service = self._DockerComposeService(
                name=self.services_args['head_service'].name,
                version=get_base_executor_version(),
                shard_id=None,
                jina_deployment_name=self.name,
                common_args=self.args,
                service_args=self.services_args['head_service'],
                pod_type=PodRoleType.HEAD,
                deployments_addresses=None,
            )

        if self.services_args['uses_before_service'] is not None:
            self.uses_before_service = self._DockerComposeService(
                name=self.services_args['uses_before_service'].name,
                version=get_base_executor_version(),
                shard_id=None,
                jina_deployment_name=self.name,
                common_args=self.args,
                service_args=self.services_args['uses_before_service'],
                pod_type=PodRoleType.WORKER,
                deployments_addresses=None,
            )

        if self.services_args['uses_after_service'] is not None:
            self.uses_after_service = self._DockerComposeService(
                name=self.services_args['uses_after_service'].name,
                version=get_base_executor_version(),
                shard_id=None,
                jina_deployment_name=self.name,
                common_args=self.args,
                service_args=self.services_args['uses_after_service'],
                pod_type=PodRoleType.WORKER,
                deployments_addresses=None,
            )

        self.worker_services = []
        services_args = self.services_args['services']
        for i, args in enumerate(services_args):
            name = f'{self.name}-{i}' if len(services_args) > 1 else f'{self.name}'
            self.worker_services.append(
                self._DockerComposeService(
                    name=name,
                    version=get_base_executor_version(),
                    shard_id=i,
                    common_args=self.args,
                    service_args=args,
                    pod_type=PodRoleType.WORKER
                    if name != 'gateway'
                    else PodRoleType.GATEWAY,
                    jina_deployment_name=self.name,
                    deployments_addresses=self.deployments_addresses
                    if name == 'gateway'
                    else None,
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
        replicas = getattr(args, 'replicas', 1)
        uses_before = getattr(args, 'uses_before', None)
        uses_after = getattr(args, 'uses_after', None)

        if args.name != 'gateway':
            parsed_args['head_service'] = BaseDeployment._copy_to_head_args(self.args)
            parsed_args['head_service'].port = port
            parsed_args['head_service'].uses = None
            parsed_args['head_service'].uses_metas = None
            parsed_args['head_service'].uses_with = None
            parsed_args['head_service'].uses_before = None
            parsed_args['head_service'].uses_after = None
            parsed_args['head_service'].env = None

            # if the k8s connection pool is disabled, the connection pool is managed manually
            import json

            connection_list = {}
            for shard_id in range(shards):
                shard_name = f'{self.name}-{shard_id}' if shards > 1 else f'{self.name}'
                connection_list[str(shard_id)] = []
                for i_rep in range(replicas):
                    replica_name = (
                        f'{shard_name}/rep-{i_rep}' if replicas > 1 else shard_name
                    )
                    connection_list[str(shard_id)].append(
                        f'{to_compatible_name(replica_name)}:{port}'
                    )

            parsed_args['head_service'].connection_list = json.dumps(connection_list)

        if uses_before:
            uses_before_cargs = copy.deepcopy(args)
            uses_before_cargs.shard_id = 0
            uses_before_cargs.replicas = 1
            uses_before_cargs.name = f'{args.name}/uses-before'
            uses_before_cargs.uses = args.uses_before
            uses_before_cargs.uses_before = None
            uses_before_cargs.uses_after = None
            uses_before_cargs.uses_with = None
            uses_before_cargs.uses_metas = None
            uses_before_cargs.env = None
            uses_before_cargs.port = port
            uses_before_cargs.uses_before_address = None
            uses_before_cargs.uses_after_address = None
            uses_before_cargs.connection_list = None
            uses_before_cargs.pod_role = PodRoleType.WORKER
            uses_before_cargs.polling = None
            parsed_args['uses_before_service'] = uses_before_cargs
            parsed_args[
                'head_service'
            ].uses_before_address = (
                f'{to_compatible_name(uses_before_cargs.name)}:{uses_before_cargs.port}'
            )
        if uses_after:
            uses_after_cargs = copy.deepcopy(args)
            uses_after_cargs.shard_id = 0
            uses_after_cargs.replicas = 1
            uses_after_cargs.name = f'{args.name}/uses-after'
            uses_after_cargs.uses = args.uses_after
            uses_after_cargs.uses_before = None
            uses_after_cargs.uses_after = None
            uses_after_cargs.uses_with = None
            uses_after_cargs.uses_metas = None
            uses_after_cargs.env = None
            uses_after_cargs.port = port
            uses_after_cargs.uses_before_address = None
            uses_after_cargs.uses_after_address = None
            uses_after_cargs.connection_list = None
            uses_after_cargs.pod_role = PodRoleType.WORKER
            uses_after_cargs.polling = None
            parsed_args['uses_after_service'] = uses_after_cargs
            parsed_args[
                'head_service'
            ].uses_after_address = (
                f'{to_compatible_name(uses_after_cargs.name)}:{uses_after_cargs.port}'
            )

        for i in range(shards):
            cargs = copy.deepcopy(args)
            cargs.shard_id = i
            cargs.uses_before = None
            cargs.uses_after = None
            cargs.k8s_connection_pool = False
            cargs.uses_before_address = None
            cargs.uses_after_address = None
            if shards > 1:
                cargs.name = f'{cargs.name}-{i}'
            if args.name == 'gateway':
                cargs.pod_role = PodRoleType.GATEWAY
            else:
                cargs.port = port
            parsed_args['services'].append(cargs)

        return parsed_args

    def to_docker_compose_config(
        self,
    ) -> List[Tuple[str, Dict]]:
        """
        Return a list of dictionary configurations. One for each service in this Deployment
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
            services = []
            if self.head_service is not None:
                services.append(
                    (
                        self.head_service.compatible_name,
                        self.head_service.get_runtime_config()[0],
                    )
                )
            if self.uses_before_service is not None:
                services.append(
                    (
                        self.uses_before_service.compatible_name,
                        self.uses_before_service.get_runtime_config()[0],
                    )
                )
            if self.uses_after_service is not None:
                services.append(
                    (
                        self.uses_after_service.compatible_name,
                        self.uses_after_service.get_runtime_config()[0],
                    )
                )
            for worker_service in self.worker_services:
                configs = worker_service.get_runtime_config()
                for rep_id, config in enumerate(configs):
                    name = (
                        f'{worker_service.name}/rep-{rep_id}'
                        if len(configs) > 1
                        else worker_service.name
                    )
                    services.append((to_compatible_name(name), config))
            return services

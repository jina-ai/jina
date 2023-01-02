import copy
import os
from argparse import Namespace
from typing import Dict, List, Optional, Tuple, Union

from jina.constants import (
    __default_composite_gateway__,
    __default_executor__,
    __default_grpc_gateway__,
    __default_http_gateway__,
    __default_websocket_gateway__,
)
from jina.enums import PodRoleType
from jina.excepts import NoContainerizedError
from jina.orchestrate.deployments import BaseDeployment
from jina.orchestrate.deployments.config.helper import (
    construct_runtime_container_args,
    get_base_executor_version,
    get_image_name,
    to_compatible_name,
    validate_uses,
)
from jina.orchestrate.helper import generate_default_volume_and_workspace

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

            cargs = copy.copy(self.service_args)

            image_name = self._get_image_name(cargs.uses)

            cargs.deployments_addresses = self.deployments_addresses
            from jina.helper import ArgNamespace
            from jina.parsers import set_gateway_parser

            taboo = {
                'uses_metas',
                'volumes',
                'uses_before',
                'uses_after',
                'workspace',
                'workspace_id',
                'noblock_on_start',
                'env',
            }

            if cargs.uses not in [
                __default_http_gateway__,
                __default_websocket_gateway__,
                __default_grpc_gateway__,
                __default_composite_gateway__,
            ]:
                cargs.uses = 'config.yml'

            non_defaults = ArgNamespace.get_non_defaults_args(
                cargs, set_gateway_parser(), taboo=taboo
            )
            _args = ArgNamespace.kwargs2list(non_defaults)

            container_args = ['gateway'] + _args

            protocol = str(non_defaults.get('protocol', ['grpc'])[0]).lower()

            ports = cargs.port + ([cargs.port_monitoring] if cargs.monitoring else [])

            envs = [f'JINA_LOG_LEVEL={os.getenv("JINA_LOG_LEVEL", "INFO")}']
            if cargs.env:
                for k, v in cargs.env.items():
                    envs.append(f'{k}={v}')
            return {
                'image': image_name,
                'entrypoint': ['jina'],
                'command': container_args,
                'expose': ports,
                'ports': [f'{_port}:{_port}' for _port in ports],
                'healthcheck': {
                    'test': f'jina ping gateway {protocol}://127.0.0.1:{cargs.port[0]}',
                    'interval': '2s',
                },
                'environment': envs,
            }

        def _get_image_name(self, uses: Optional[str]):
            import os

            image_name = os.getenv(
                'JINA_GATEWAY_IMAGE', f'jinaai/jina:{self.version}-py38-standard'
            )

            if uses is not None and uses not in [
                __default_executor__,
                __default_http_gateway__,
                __default_websocket_gateway__,
                __default_grpc_gateway__,
                __default_composite_gateway__,
            ]:
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

        def _update_config_with_volumes(self, config, auto_volume=True):
            if self.service_args.volumes:  # respect custom volume definition
                config['volumes'] = self.service_args.volumes
                return config

            if not auto_volume:
                return config

            # if no volume is given, create default volume
            (
                generated_volumes,
                workspace_in_container,
            ) = generate_default_volume_and_workspace(
                workspace_id=self.service_args.workspace_id
            )
            config['volumes'] = generated_volumes
            if (
                '--workspace' not in config['command']
            ):  # set workspace only of not already given
                config['command'].append('--workspace')
                config['command'].append(workspace_in_container)
            return config

        def get_runtime_config(self) -> List[Dict]:
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
                    'healthcheck': {
                        'test': f'jina ping executor 127.0.0.1:{cargs.port}',
                        'interval': '2s',
                    },
                    'environment': [
                        f'JINA_LOG_LEVEL={os.getenv("JINA_LOG_LEVEL", "INFO")}'
                    ],
                }

                if cargs.gpus:
                    try:
                        count = int(cargs.gpus)
                    except ValueError:
                        count = cargs.gpus

                    config['deploy'] = {
                        'resources': {
                            'reservations': {
                                'devices': [
                                    {
                                        'driver': 'nvidia',
                                        'count': count,
                                        'capabilities': ['gpu'],
                                    }
                                ]
                            }
                        }
                    }

                if cargs.monitoring:
                    config['expose'] = [cargs.port_monitoring]
                    config['ports'] = [
                        f'{cargs.port_monitoring}:{cargs.port_monitoring}'
                    ]

                if env is not None:
                    config['environment'] = [f'{k}={v}' for k, v in env.items()]

                if self.service_args.pod_role == PodRoleType.WORKER:
                    config = self._update_config_with_volumes(
                        config, auto_volume=not self.common_args.disable_auto_volume
                    )

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

        if args.name != 'gateway' and shards > 1:
            parsed_args['head_service'] = BaseDeployment._copy_to_head_args(self.args)
            parsed_args['head_service'].port = port
            parsed_args['head_service'].uses = None
            parsed_args['head_service'].uses_metas = None
            parsed_args['head_service'].uses_with = None
            parsed_args['head_service'].uses_before = None
            parsed_args['head_service'].uses_after = None

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

        if uses_before and shards > 1:
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
            uses_before_cargs.host = args.host[0]
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
        if uses_after and shards > 1:
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
            uses_after_cargs.host = args.host[0]
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
            cargs.uses_before_address = None
            cargs.uses_after_address = None
            if shards > 1:
                cargs.name = f'{cargs.name}-{i}'
            if args.name == 'gateway':
                cargs.pod_role = PodRoleType.GATEWAY
            else:
                cargs.port = port
                cargs.host = args.host[0]
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

import copy
from abc import abstractmethod
from argparse import Namespace
from contextlib import ExitStack
from itertools import cycle
from typing import Dict, Union, Set, List, Optional

from .. import Pea
from ..networking import GrpcConnectionPool
from ..peas.factory import PeaFactory
from ... import __default_executor__, __default_host__
from ... import helper
from ...enums import (
    PodRoleType,
    PeaRoleType,
    PollingType,
)
from ...excepts import RuntimeFailToStart, RuntimeRunForeverEarlyError, ScalingFails
from ...helper import random_identity, CatchAllCleanupContextManager
from ...jaml.helper import complete_path
from .k8slib import kubernetes_deployment, kubernetes_client
from ..networking import K8sGrpcConnectionPool


class PodConfig:
    class _K8sDeployment:
        def __init__(
            self,
            name: str,
            head_port_in: int,
            version: str,
            pea_type: str,
            jina_pod_name: str,
            shard_id: Optional[int],
            common_args: Union['Namespace', Dict],
            deployment_args: Union['Namespace', Dict],
        ):
            self.name = name
            self.dns_name = kubernetes_deployment.to_dns_name(name)
            self.head_port_in = head_port_in
            self.version = version
            self.pea_type = pea_type
            self.jina_pod_name = jina_pod_name
            self.shard_id = shard_id
            self.common_args = common_args
            self.deployment_args = deployment_args
            self.k8s_namespace = self.common_args.k8s_namespace
            self.num_replicas = getattr(self.deployment_args, 'replicas', 1)
            self.cluster_address = None

        def _create_gateway_yamls(self):
            import os

            test_pip = os.getenv('JINA_K8S_USE_TEST_PIP') is not None
            image_name = (
                'jinaai/jina:test-pip'
                if test_pip
                else f'jinaai/jina:{self.version}-py38-standard'
            )
            kubernetes_deployment.deploy_service(
                self.dns_name,
                namespace=self.k8s_namespace,
                image_name=image_name,
                container_cmd='["jina"]',
                container_args=f'["gateway", '
                f'{kubernetes_deployment.get_cli_params(arguments=self.common_args, skip_list=("pod_role",))}]',
                replicas=1,
                pull_policy='IfNotPresent',
                jina_pod_name='gateway',
                pea_type='gateway',
                port_expose=self.common_args.port_expose,
            )

        @staticmethod
        def _construct_runtime_container_args(
            deployment_args, uses, uses_metas, uses_with_string, pea_type, port_in
        ):
            container_args = (
                f'["executor", '
                f'"--native", '
                f'"--uses", "{uses}", '
                f'"--runtime-cls", {"WorkerRuntime" if pea_type.lower() == "worker" else "HeadRuntime"}, '
                f'"--uses-metas", "{uses_metas}", '
                + uses_with_string
                + f'{kubernetes_deployment.get_cli_params(arguments=deployment_args, port_in=port_in)}]'
            )
            return container_args

        def _get_image_name(self, uses: str):
            image_name = kubernetes_deployment.get_image_name(uses)
            if image_name == __default_executor__:
                test_pip = os.getenv('JINA_K8S_USE_TEST_PIP') is not None
                image_name = (
                    'jinaai/jina:test-pip'
                    if test_pip
                    else f'jinaai/jina:{self.version}-py38-perf'
                )

            return image_name

        def _get_init_container_args(self):
            return kubernetes_deployment.get_init_container_args(self.common_args)

        def _get_container_args(self, uses, pea_type=None, port_in=None):
            uses_metas = kubernetes_deployment.dictionary_to_cli_param(
                {'pea_id': self.shard_id}
            )
            uses_with = kubernetes_deployment.dictionary_to_cli_param(
                self.deployment_args.uses_with
            )
            uses_with_string = f'"--uses-with", "{uses_with}", ' if uses_with else ''
            if uses != __default_executor__:
                uses = 'config.yml'
            return self._construct_runtime_container_args(
                self.deployment_args,
                uses,
                uses_metas,
                uses_with_string,
                pea_type if pea_type else self.pea_type,
                port_in,
            )

        def _deploy_runtime(
            self,
            replace=False,
        ):
            image_name = self._get_image_name(self.deployment_args.uses)
            image_name_uses_before = (
                self._get_image_name(self.deployment_args.uses_before)
                if hasattr(self.deployment_args, 'uses_before')
                and self.deployment_args.uses_before
                else None
            )
            image_name_uses_after = (
                self._get_image_name(self.deployment_args.uses_after)
                if hasattr(self.deployment_args, 'uses_after')
                and self.deployment_args.uses_after
                else None
            )
            init_container_args = self._get_init_container_args()
            container_args = self._get_container_args(self.deployment_args.uses)
            container_args_uses_before = (
                self._get_container_args(
                    self.deployment_args.uses_before,
                    'worker',
                    port_in=K8sGrpcConnectionPool.K8S_PORT_USES_BEFORE,
                )
                if hasattr(self.deployment_args, 'uses_before')
                and self.deployment_args.uses_before
                else None
            )
            container_args_uses_after = (
                self._get_container_args(
                    self.deployment_args.uses_after,
                    'worker',
                    port_in=K8sGrpcConnectionPool.K8S_PORT_USES_AFTER,
                )
                if hasattr(self.deployment_args, 'uses_after')
                and self.deployment_args.uses_after
                else None
            )

            self.cluster_address = kubernetes_deployment.deploy_service(
                self.dns_name,
                namespace=self.k8s_namespace,
                image_name=image_name,
                image_name_uses_after=image_name_uses_after,
                image_name_uses_before=image_name_uses_before,
                container_cmd='["jina"]',
                container_cmd_uses_before='["jina"]',
                container_cmd_uses_after='["jina"]',
                container_args=container_args,
                container_args_uses_before=container_args_uses_before,
                container_args_uses_after=container_args_uses_after,
                logger=JinaLogger(f'deploy_{self.name}'),
                replicas=self.num_replicas,
                pull_policy='IfNotPresent',
                jina_pod_name=self.jina_pod_name,
                pea_type=self.pea_type,
                shard_id=self.shard_id,
                init_container=init_container_args,
                env=self.deployment_args.env,
                gpus=self.deployment_args.gpus
                if hasattr(self.deployment_args, 'gpus')
                else None,
                custom_resource_dir=getattr(
                    self.common_args, 'k8s_custom_resource_dir', None
                ),
                replace_deployment=replace,
            )

    def _get_deployment_args(self, args):
        parsed_args = {
            'head_deployment': None,
            'deployments': [],
        }
        shards = getattr(args, 'shards', 1)
        uses_before = getattr(args, 'uses_before', None)
        uses_after = getattr(args, 'uses_after', None)

        if args.name != 'gateway':
            parsed_args['head_deployment'] = copy.copy(args)
            parsed_args['head_deployment'].replicas = 1
            parsed_args['head_deployment'].runtime_cls = 'HeadRuntime'
            parsed_args['head_deployment'].pea_role = PeaRoleType.HEAD
            parsed_args['head_deployment'].port_in = K8sGrpcConnectionPool.K8S_PORT_IN

            # if the k8s connection pool is disabled, the connection pool is managed manually
            if not args.k8s_connection_pool:
                connection_list = '{'
                for i in range(shards):
                    name = f'{self.name}-{i}' if shards > 1 else f'{self.name}'
                    connection_list += f'"{str(i)}": "{name}.{self.k8s_namespace}.svc:{K8sGrpcConnectionPool.K8S_PORT_IN}",'
                connection_list = connection_list[:-1]
                connection_list += '}'

                parsed_args['head_deployment'].connection_list = connection_list

        if uses_before:
            parsed_args[
                'head_deployment'
            ].uses_before_address = (
                f'127.0.0.1:{K8sGrpcConnectionPool.K8S_PORT_USES_BEFORE}'
            )
        if uses_after:
            parsed_args[
                'head_deployment'
            ].uses_after_address = (
                f'127.0.0.1:{K8sGrpcConnectionPool.K8S_PORT_USES_AFTER}'
            )

        for i in range(shards):
            cargs = copy.deepcopy(args)
            cargs.shard_id = i
            cargs.uses_before = None
            cargs.uses_after = None
            cargs.port_in = K8sGrpcConnectionPool.K8S_PORT_IN
            if args.name == 'gateway':
                cargs.pea_role = PeaRoleType.GATEWAY
            parsed_args['deployments'].append(cargs)

        return parsed_args

    def _get_base_executor_version(self):
        from jina import __version__
        import requests

        url = 'https://registry.hub.docker.com/v1/repositories/jinaai/jina/tags'
        tags = requests.get(url).json()
        name_set = {tag['name'] for tag in tags}
        if __version__ in name_set:
            return __version__
        else:
            return 'master'

    @property
    @abstractmethod
    def name(self) -> str:
        """the name of the Pod"""
        ...

    @property
    @abstractmethod
    def args(self) -> Union['Namespace', Dict]:
        """The args to be given to the Pod"""
        ...

    @property
    def head_deployment(self):
        if self._get_deployment_args(self.args)['head_deployment'] is not None:
            name = f'{self.name}-head'
            return self._K8sDeployment(
                name=name,
                head_port_in=K8sGrpcConnectionPool.K8S_PORT_IN,
                version=self._get_base_executor_version(),
                shard_id=None,
                jina_pod_name=self.name,
                common_args=self.args,
                deployment_args=self.head_args,
                pea_type='head',
            )

    def worker_deployments(self) -> List['PodConfig._K8sDeployment']:
        deployments = []
        deployment_args = self.self._get_deployment_args(self.args)['deployments']
        for i, args in enumerate(deployment_args):
            name = f'{self.name}-{i}' if len(deployment_args) > 1 else f'{self.name}'
            deployments.append(
                self._K8sDeployment(
                    name=name,
                    head_port_in=K8sGrpcConnectionPool.K8S_PORT_IN,
                    version=self._get_base_executor_version(),
                    shard_id=i,
                    common_args=self.args,
                    deployment_args=args,
                    pea_type='worker',
                    jina_pod_name=self.name,
                )
            )
        return deployments

    def k8s_namespace(self) -> str:
        """The k8s namespace"""
        return self.args.k8s_namespace

    def to_k8s_yaml(self) -> List[Dict]:
        """
        Return a list of dictionary configurations. One for each deployment in this Pod
        """
        if self.name == 'gateway':
            return self._get_gateway_yamls()
        else:
            return self._get_deployments_yamls()

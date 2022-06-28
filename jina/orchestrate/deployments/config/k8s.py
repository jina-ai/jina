import copy
from argparse import Namespace
from typing import Dict, List, Optional, Tuple, Union

from jina import __default_executor__
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
from jina.orchestrate.deployments.config.k8slib import kubernetes_deployment
from jina.serve.networking import GrpcConnectionPool


class K8sDeploymentConfig:
    """
    Class that implements the output of configuration files for Kubernetes for a given Deployment.
    """

    class _K8sDeployment:
        def __init__(
            self,
            name: str,
            version: str,
            pod_type: PodRoleType,
            jina_deployment_name: str,
            shard_id: Optional[int],
            common_args: Union['Namespace', Dict],
            deployment_args: Union['Namespace', Dict],
            k8s_namespace: str,
            k8s_deployments_addresses: Optional[Dict[str, List[str]]] = None,
        ):
            self.name = name
            self.dns_name = to_compatible_name(name)
            self.version = version
            self.pod_type = pod_type
            self.jina_deployment_name = jina_deployment_name
            self.shard_id = shard_id
            self.common_args = common_args
            self.deployment_args = deployment_args
            self.num_replicas = getattr(self.deployment_args, 'replicas', 1)
            self.k8s_namespace = k8s_namespace
            self.k8s_deployments_addresses = k8s_deployments_addresses

        def get_gateway_yamls(
            self,
        ) -> List[Dict]:
            import os

            image_name = os.getenv(
                'JINA_GATEWAY_IMAGE', f'jinaai/jina:{self.version}-py38-standard'
            )

            cargs = copy.copy(self.deployment_args)
            cargs.deployments_addresses = self.k8s_deployments_addresses
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
                'env',
            }

            non_defaults = ArgNamespace.get_non_defaults_args(
                cargs, set_gateway_parser(), taboo=taboo
            )
            _args = ArgNamespace.kwargs2list(non_defaults)
            container_args = ['gateway'] + _args
            return kubernetes_deployment.get_deployment_yamls(
                self.dns_name,
                namespace=self.k8s_namespace,
                image_name=image_name,
                container_cmd='["jina"]',
                container_args=f'{container_args}',
                replicas=1,
                pull_policy='IfNotPresent',
                jina_deployment_name='gateway',
                pod_type=self.pod_type,
                port=self.common_args.port,
                env=cargs.env,
                monitoring=self.common_args.monitoring,
                port_monitoring=self.common_args.port_monitoring,
            )

        def _get_image_name(self, uses: Optional[str]):
            import os

            image_name = os.getenv(
                'JINA_GATEWAY_IMAGE', f'jinaai/jina:{self.version}-py38-standard'
            )

            if uses is not None and uses != __default_executor__:
                image_name = get_image_name(uses)

            return image_name

        def _get_container_args(self, cargs, pod_type):
            uses_metas = cargs.uses_metas or {}
            uses_with = self.deployment_args.uses_with
            if cargs.uses != __default_executor__:
                cargs.uses = 'config.yml'
            return construct_runtime_container_args(
                cargs, uses_metas, uses_with, pod_type
            )

        def get_runtime_yamls(
            self,
        ) -> List[Dict]:
            cargs = copy.copy(self.deployment_args)

            image_name = self._get_image_name(cargs.uses)
            image_name_uses_before = (
                self._get_image_name(cargs.uses_before)
                if hasattr(cargs, 'uses_before') and cargs.uses_before
                else None
            )
            image_name_uses_after = (
                self._get_image_name(cargs.uses_after)
                if hasattr(cargs, 'uses_after') and cargs.uses_after
                else None
            )
            container_args = self._get_container_args(cargs, pod_type=self.pod_type)
            container_args_uses_before = None
            if getattr(cargs, 'uses_before', False):
                uses_before_cargs = copy.copy(cargs)
                uses_before_cargs.uses = cargs.uses_before
                uses_before_cargs.name = f'{self.common_args.name}/uses-before'
                uses_before_cargs.port = GrpcConnectionPool.K8S_PORT_USES_BEFORE
                uses_before_cargs.uses_before_address = None
                uses_before_cargs.uses_after_address = None
                uses_before_cargs.uses_before = None
                uses_before_cargs.uses_after = None
                uses_before_cargs.uses_with = None
                uses_before_cargs.uses_metas = None
                uses_before_cargs.connection_list = None
                uses_before_cargs.runtime_cls = 'WorkerRuntime'
                uses_before_cargs.pod_role = PodRoleType.WORKER
                uses_before_cargs.polling = None
                uses_before_cargs.env = None
                container_args_uses_before = self._get_container_args(
                    uses_before_cargs, PodRoleType.WORKER
                )

            container_args_uses_after = None
            if getattr(cargs, 'uses_after', False):
                uses_after_cargs = copy.copy(cargs)
                uses_after_cargs.uses = cargs.uses_after
                uses_after_cargs.name = f'{self.common_args.name}/uses-after'
                uses_after_cargs.port = GrpcConnectionPool.K8S_PORT_USES_AFTER
                uses_after_cargs.uses_before_address = None
                uses_after_cargs.uses_after_address = None
                uses_after_cargs.uses_before = None
                uses_after_cargs.uses_after = None
                uses_after_cargs.uses_with = None
                uses_after_cargs.uses_metas = None
                uses_after_cargs.connection_list = None
                uses_after_cargs.runtime_cls = 'WorkerRuntime'
                uses_after_cargs.pod_role = PodRoleType.WORKER
                uses_after_cargs.polling = None
                uses_after_cargs.env = None
                container_args_uses_after = self._get_container_args(
                    uses_after_cargs, PodRoleType.WORKER
                )

            return kubernetes_deployment.get_deployment_yamls(
                self.dns_name,
                namespace=self.k8s_namespace,
                image_name=image_name,
                image_name_uses_after=image_name_uses_after,
                image_name_uses_before=image_name_uses_before,
                container_cmd='["jina"]',
                container_cmd_uses_before='["jina"]',
                container_cmd_uses_after='["jina"]',
                container_args=f'{container_args}',
                container_args_uses_before=container_args_uses_before,
                container_args_uses_after=container_args_uses_after,
                replicas=self.num_replicas,
                pull_policy='IfNotPresent',
                jina_deployment_name=self.jina_deployment_name,
                pod_type=self.pod_type,
                shard_id=self.shard_id,
                env=cargs.env,
                gpus=cargs.gpus if hasattr(cargs, 'gpus') else None,
                monitoring=cargs.monitoring,
                port_monitoring=cargs.port_monitoring,
            )

    def __init__(
        self,
        args: Union['Namespace', Dict],
        k8s_namespace: Optional[str] = None,
        k8s_deployments_addresses: Optional[Dict[str, List[str]]] = None,
    ):
        # External Deployments should be ignored in a K8s based Flow
        assert not (hasattr(args, 'external') and args.external)
        if not validate_uses(args.uses):
            raise NoContainerizedError(
                f'Executor "{args.uses}" is not valid to be used in K8s. '
                'You need to use a containerized Executor. You may check `jina hub --help` to see how Jina Hub can help you building containerized Executors.'
            )
        self.k8s_namespace = k8s_namespace
        self.k8s_deployments_addresses = k8s_deployments_addresses
        self.head_deployment = None
        self.args = copy.copy(args)
        if k8s_namespace is not None:
            # otherwise it will remain with the one from the original Deployment
            self.args.k8s_namespace = k8s_namespace
        self.name = self.args.name

        self.deployment_args = self._get_deployment_args(self.args)

        if self.deployment_args['head_deployment'] is not None:
            self.head_deployment = self._K8sDeployment(
                name=self.deployment_args['head_deployment'].name,
                version=get_base_executor_version(),
                shard_id=None,
                jina_deployment_name=self.name,
                common_args=self.args,
                deployment_args=self.deployment_args['head_deployment'],
                pod_type=PodRoleType.HEAD,
                k8s_namespace=self.k8s_namespace,
                k8s_deployments_addresses=self.k8s_deployments_addresses,
            )

        self.worker_deployments = []
        deployment_args = self.deployment_args['deployments']
        for i, args in enumerate(deployment_args):
            name = f'{self.name}-{i}' if len(deployment_args) > 1 else f'{self.name}'
            self.worker_deployments.append(
                self._K8sDeployment(
                    name=name,
                    version=get_base_executor_version(),
                    shard_id=i,
                    common_args=self.args,
                    deployment_args=args,
                    pod_type=PodRoleType.WORKER
                    if name != 'gateway'
                    else PodRoleType.GATEWAY,
                    jina_deployment_name=self.name,
                    k8s_namespace=self.k8s_namespace,
                    k8s_deployments_addresses=self.k8s_deployments_addresses
                    if name == 'gateway'
                    else None,
                )
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
            # head deployment only exists for sharded deployments
            if shards > 1:
                parsed_args['head_deployment'] = BaseDeployment._copy_to_head_args(
                    self.args
                )
                parsed_args['head_deployment'].gpus = None
                parsed_args['head_deployment'].port = GrpcConnectionPool.K8S_PORT
                parsed_args[
                    'head_deployment'
                ].port_monitoring = GrpcConnectionPool.K8S_PORT_MONITORING
                parsed_args['head_deployment'].uses = None
                parsed_args['head_deployment'].uses_metas = None
                parsed_args['head_deployment'].uses_with = None

                import json

                connection_list = {}
                for i in range(shards):
                    name = (
                        f'{to_compatible_name(self.name)}-{i}'
                        if shards > 1
                        else f'{to_compatible_name(self.name)}'
                    )
                    connection_list[
                        str(i)
                    ] = f'{name}.{self.k8s_namespace}.svc:{GrpcConnectionPool.K8S_PORT}'

                parsed_args['head_deployment'].connection_list = json.dumps(
                    connection_list
                )

                if uses_before:
                    parsed_args[
                        'head_deployment'
                    ].uses_before_address = (
                        f'127.0.0.1:{GrpcConnectionPool.K8S_PORT_USES_BEFORE}'
                    )
                if uses_after:
                    parsed_args[
                        'head_deployment'
                    ].uses_after_address = (
                        f'127.0.0.1:{GrpcConnectionPool.K8S_PORT_USES_AFTER}'
                    )

        for i in range(shards):
            cargs = copy.deepcopy(args)
            cargs.shard_id = i
            cargs.uses_before = None
            cargs.uses_after = None
            if args.name != 'gateway':
                cargs.port = GrpcConnectionPool.K8S_PORT
                cargs.port_monitoring = GrpcConnectionPool.K8S_PORT_MONITORING

            cargs.uses_before_address = None
            cargs.uses_after_address = None
            if shards > 1:
                cargs.name = f'{cargs.name}-{i}'
            if args.name == 'gateway':
                cargs.pod_role = PodRoleType.GATEWAY
            parsed_args['deployments'].append(cargs)

        return parsed_args

    def to_kubernetes_yaml(
        self,
    ) -> List[Tuple[str, List[Dict]]]:
        """
        Return a list of dictionary configurations. One for each deployment in this Deployment
            .. # noqa: DAR201
            .. # noqa: DAR101
        """
        if self.name == 'gateway':
            return [
                (
                    'gateway',
                    self.worker_deployments[0].get_gateway_yamls(),
                )
            ]
        else:
            deployments = []
            if self.head_deployment:
                deployments.append(self.head_deployment)
            deployments.extend(self.worker_deployments)
            return [
                (
                    deployment.dns_name,
                    deployment.get_runtime_yamls(),
                )
                for deployment in deployments
            ]

    to_k8s_yaml = to_kubernetes_yaml

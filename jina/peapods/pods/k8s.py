import copy
from argparse import Namespace
from typing import Optional, Dict, Union, Set, List

from .k8slib import kubernetes_deployment, kubernetes_tools
from .. import BasePod
from ... import __default_executor__
from ...logging.logger import JinaLogger


class K8sPod(BasePod):
    def __init__(
            self, args: Union['Namespace', Dict], needs: Optional[Set[str]] = None
    ):
        super().__init__()
        self.args = args
        self.needs = needs or set()
        self.deployment_args = self._parse_args(args)

    def _parse_args(
            self, args: Namespace
    ) -> Dict[str, Optional[Union[List[Namespace], Namespace]]]:
        return self._parse_deployment_args(args)

    def _parse_deployment_args(self, args):
        parsed_args = {
            'head_deployment': None,
            'tail_deployment': None,
            'deployments': [],
        }
        parallel = getattr(args, 'parallel', 1)
        if parallel > 1:
            # reasons to separate head and tail from peas is that they
            # can be deducted based on the previous and next pods
            parsed_args['head_deployment'] = copy.copy(args)
            parsed_args['head_deployment'].uses = args.uses_before
            parsed_args['tail_deployment'] = copy.copy(args)
            parsed_args['tail_deployment'].uses = args.uses_after
            parsed_args['deployments'] = [args] * parallel
        else:
            parsed_args['deployments'] = [args]
        return parsed_args

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
        self.join()

    @property
    def port_expose(self) -> int:
        raise NotImplementedError

    @property
    def host(self) -> str:
        raise NotImplementedError

    def _deploy_gateway(self):
        kubernetes_deployment.deploy_service(
            self.name,
            namespace=self.args.k8s_namespace,  # maybe new args for kubernetes Pod
            port_in=self.args.port_in,
            port_out=self.args.port_out,
            port_ctrl=self.args.port_ctrl,
            port_expose=self.args.port_expose,
            image_name='jinaai/jina:master-py38-standard',
            container_cmd='["jina"]',
            container_args=f'["gateway", '
                           f'"--grpc-data-requests", '
                           f'"--runtime-cls", "GRPCDataRuntime", '
                           f'{kubernetes_deployment.get_cli_params(self.args, ("pod_role",))}]',
            logger=JinaLogger(f'deploy_{self.name}'),
            replicas=1,
            pull_policy='Always',
            init_container=None,
        )

    def _deploy_runtime(self, deployment_args, replicas, k8s_namespace, deployment_id):
        image_name = kubernetes_deployment.get_image_name(self.args.uses)
        name_suffix = self.name + ('-' + str(deployment_id) if self.args.parallel > 1 else '')
        dns_name = kubernetes_deployment.to_dns_name(name_suffix)
        init_container_args = kubernetes_deployment.get_init_container_args(self)
        uses_metas = kubernetes_deployment.dictionary_to_cli_param(
            {'pea_id': deployment_id}
        )
        uses_with = kubernetes_deployment.dictionary_to_cli_param(self.args.uses_with)
        uses_with_string = f'"--uses-with", "{uses_with}", ' if uses_with else ''
        if image_name == __default_executor__:
            image_name = 'gcr.io/jina-showcase/custom-jina:latest'
            container_args = (
                    f'["pea", '
                    f'"--uses", "BaseExecutor", '
                    f'"--grpc-data-requests", '
                    f'"--runtime-cls", "GRPCDataRuntime", '
                    f'"--uses-metas", "{uses_metas}", '
                    + uses_with_string
                    + f'{kubernetes_deployment.get_cli_params(self.args)}]'
            )

        else:
            container_args = (
                    f'["pea", '
                    f'"--uses", "config.yml", '
                    f'"--grpc-data-requests", '
                    f'"--runtime-cls", "GRPCDataRuntime", '
                    f'"--uses-metas", "{uses_metas}", '
                    + uses_with_string
                    + f'{kubernetes_deployment.get_cli_params(self.args)}]'
            )

        kubernetes_deployment.deploy_service(
            dns_name,
            namespace=k8s_namespace,  # maybe new args for kubernetes Pod
            port_in=deployment_args.port_in,
            port_out=deployment_args.port_out,
            port_ctrl=deployment_args.port_ctrl,
            port_expose=deployment_args.port_expose,
            image_name=image_name,
            container_cmd='["jina"]',
            container_args=container_args,
            logger=JinaLogger(f'deploy_{self.name}'),
            replicas=replicas,
            pull_policy='IfNotPresent',  # TODO: Parameterize
            init_container=init_container_args,
        )

    def start(self) -> 'K8sPod':
        # K8s start things
        kubernetes_tools.create('namespace', {'name': self.args.k8s_namespace})

        if self.name == 'gateway':
            self._deploy_gateway()
        else:
            if self.deployment_args['head_deployment'] is not None:
                self._deploy_runtime(
                    self.deployment_args['head_deployment'],
                    1,
                    self.args.k8s_namespace,
                    '_head',
                )

            for i in range(self.args.parallel):
                deployment_args = self.deployment_args['deployments'][i]
                self._deploy_runtime(
                    deployment_args, self.args.replicas, self.args.k8s_namespace, i
                )

            if self.deployment_args['tail_deployment'] is not None:
                self._deploy_runtime(
                    self.deployment_args['tail_deployment'],
                    1,
                    self.args.k8s_namespace,
                    '_tail',
                )

    def wait_start_success(self) -> None:
        # if eventually we can check when the start is good
        pass

    def close(self):
        # kill properly the deployments
        pass

    def join(self):
        # Wait to make sure deployments are properly killed
        pass

    @property
    def is_ready(self) -> bool:
        # if eventually we can check when the start is good
        return True

    @property
    def head_args(self) -> Namespace:
        return self.args

    @property
    def tail_args(self) -> Namespace:
        return self.args

    def is_singleton(self) -> bool:
        return True  # only used in plot now

    @property
    def num_peas(self):
        return -1

    @property
    def head_zmq_identity(self):
        return b''

    @property
    def deployments(self):
        res = []
        if self.args.name == 'gateway':
            name = kubernetes_deployment.to_dns_name(self.name)
            res.append(
                {
                    'name': f'{self.name}',
                    'head_host': f'{name}.{self.args.k8s_namespace}.svc.cluster.local',
                    'head_port_in': 8081,
                    'tail_port_out': 8082,
                    'head_zmq_identity': self.head_zmq_identity,
                }
            )
        else:
            if self.deployment_args['head_deployment'] is not None:
                name = kubernetes_deployment.to_dns_name(self.name + '_head')
                res.append(
                    {
                        'name': f'{self.name}_head',
                        'head_host': f'{name}.{self.args.k8s_namespace}.svc.cluster.local',
                        'head_port_in': 8081,
                        'tail_port_out': 8082,
                        'head_zmq_identity': self.head_zmq_identity,
                    }
                )
            for deployment_id, deployment_arg in enumerate(
                    self.deployment_args['deployments']
            ):
                service_name = self.name + (
                    '-' + str(deployment_id) if len(self.deployment_args['deployments']) > 1 else '')
                name = kubernetes_deployment.to_dns_name(service_name)
                name_suffix = f'_{deployment_id}' if len(self.deployment_args['deployments']) > 1 else ''
                res.append(
                    {
                        'name': f'{self.name}{name_suffix}',
                        'head_host': f'{name}.{self.args.k8s_namespace}.svc.cluster.local',
                        'head_port_in': 8081,
                        'tail_port_out': 8082,
                        'head_zmq_identity': self.head_zmq_identity,
                    }
                )
            if self.deployment_args['tail_deployment'] is not None:
                name = kubernetes_deployment.to_dns_name(self.name + '_tail')
                res.append(
                    {
                        'name': f'{self.name}_tail',
                        'head_host': f'{name}.{self.args.k8s_namespace}.svc.cluster.local',
                        'head_port_in': 8081,
                        'tail_port_out': 8082,
                        'head_zmq_identity': self.head_zmq_identity,
                    }
                )
        return res

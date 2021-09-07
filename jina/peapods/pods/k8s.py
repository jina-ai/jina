import copy
from argparse import Namespace
from typing import Optional, Dict, Union, Set, List

import jina
from .k8slib import kubernetes_deployment, kubernetes_tools
from .. import BasePod
from ... import __default_executor__
from ...logging.logger import JinaLogger


class K8sPod(BasePod):
    """The K8sPod (KubernetesPod)  is used for deployments on Kubernetes."""

    def __init__(
        self, args: Union['Namespace', Dict], needs: Optional[Set[str]] = None
    ):
        super().__init__()
        self.args = args
        self.needs = needs or set()
        self.deployment_args = self._parse_args(args)
        self.version = self._get_base_executor_version()

        self.fixed_head_port_in = 8081
        self.fixed_tail_port_out = 8082

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
            parsed_args['head_deployment'].uses = (
                args.uses_before or __default_executor__
            )
            parsed_args['tail_deployment'] = copy.copy(args)
            parsed_args['tail_deployment'].uses = (
                args.uses_after or __default_executor__
            )
            parsed_args['deployments'] = [args] * parallel
        else:
            parsed_args['deployments'] = [args]
        return parsed_args

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
        self.join()

    @property
    def port_expose(self) -> int:
        """Not implemented"""
        raise NotImplementedError

    @property
    def host(self) -> str:
        """Not implemented"""
        raise NotImplementedError

    def _deploy_gateway(self):
        kubernetes_deployment.deploy_service(
            self.name,
            namespace=self.args.k8s_namespace,
            image_name=f'jinaai/jina:{self.version}-py38-standard',
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

    def _deploy_runtime(self, deployment_args, replicas, deployment_id):
        image_name = kubernetes_deployment.get_image_name(deployment_args.uses)
        name_suffix = self.name + (
            ('-' + str(deployment_id)) if self.args.parallel > 1 else ''
        )
        dns_name = kubernetes_deployment.to_dns_name(name_suffix)
        init_container_args = kubernetes_deployment.get_init_container_args(self)
        uses_metas = kubernetes_deployment.dictionary_to_cli_param(
            {'pea_id': deployment_id}
        )
        uses_with = kubernetes_deployment.dictionary_to_cli_param(
            deployment_args.uses_with
        )
        uses_with_string = f'"--uses-with", "{uses_with}", ' if uses_with else ''
        if image_name == __default_executor__:
            image_name = f'jinaai/jina:{self.version}-py38-standard'
            uses = 'BaseExecutor'
        else:
            uses = 'config.yml'
        container_args = self._construct_runtime_container_args(
            deployment_args, uses, uses_metas, uses_with_string
        )

        kubernetes_deployment.deploy_service(
            dns_name,
            namespace=self.args.k8s_namespace,
            image_name=image_name,
            container_cmd='["jina"]',
            container_args=container_args,
            logger=JinaLogger(f'deploy_{self.name}'),
            replicas=replicas,
            pull_policy='IfNotPresent',
            init_container=init_container_args,
            custom_resource_dir=getattr(self.args, 'k8s_custom_resource_dir', None),
        )

    @staticmethod
    def _construct_runtime_container_args(
        deployment_args, uses, uses_metas, uses_with_string
    ):
        container_args = (
            f'["pea", '
            f'"--uses", "{uses}", '
            f'"--grpc-data-requests", '
            f'"--runtime-cls", "GRPCDataRuntime", '
            f'"--uses-metas", "{uses_metas}", '
            + uses_with_string
            + f'{kubernetes_deployment.get_cli_params(deployment_args)}]'
        )
        return container_args

    def start(self) -> 'K8sPod':
        """Deploy the kubernetes pods via k8s Deployment and k8s Service.

        :return: self
        """
        kubernetes_tools.create(
            'namespace',
            {'name': self.args.k8s_namespace},
            custom_resource_dir=getattr(self.args, 'k8s_custom_resource_dir', None),
        )
        if self.name == 'gateway':
            self._deploy_gateway()
        else:
            if self.deployment_args['head_deployment'] is not None:
                self._deploy_runtime(self.deployment_args['head_deployment'], 1, 'head')

            for i in range(self.args.parallel):
                deployment_args = self.deployment_args['deployments'][i]
                self._deploy_runtime(deployment_args, self.args.replicas, i)

            if self.deployment_args['tail_deployment'] is not None:
                self._deploy_runtime(self.deployment_args['tail_deployment'], 1, 'tail')
        return self

    def wait_start_success(self):
        """Not implemented. It should wait until the deployment is up and running"""
        pass

    def close(self):
        """Not implemented. It should delete the namespace of the flow"""
        pass

    def join(self):
        """Not implemented. It should wait to make sure deployments are properly killed."""
        pass

    @property
    def is_ready(self) -> bool:
        """Not implemented. It assumes it is ready.

        :return: True
        """
        return True

    @property
    def head_args(self) -> Namespace:
        """Head args of the pod.

        :return: namespace
        """
        return self.args

    @property
    def tail_args(self) -> Namespace:
        """Tail args of the pod

        :return: namespace
        """
        return self.args

    def is_singleton(self) -> bool:
        """The k8s pod is always a singleton

        :return: True
        """
        return True

    @property
    def num_peas(self) -> int:
        """Number of peas. Currently unused.

        :return: number of peas
        """
        return -1

    @property
    def head_zmq_identity(self) -> bytes:
        """zmq identity is not needed for k8s deployment

        :return: zmq identity
        """
        return b''

    @property
    def deployments(self) -> List[Dict]:
        """Deployment information which describes the interface of the pod.

        :return: list of dictionaries defining the attributes used by the routing table
        """
        res = []
        if self.args.name == 'gateway':
            res.append(self._create_node(''))
        else:
            if self.deployment_args['head_deployment'] is not None:
                res.append(self._create_node('head'))
            for deployment_id, deployment_arg in enumerate(
                self.deployment_args['deployments']
            ):
                name_suffix = (
                    deployment_id
                    if len(self.deployment_args['deployments']) > 1
                    else ''
                )
                res.append(self._create_node(name_suffix))
            if self.deployment_args['tail_deployment'] is not None:
                res.append(self._create_node('tail'))
        return res

    def _get_base_executor_version(self):
        import requests

        url = 'https://registry.hub.docker.com/v1/repositories/jinaai/jina/tags'
        tags = requests.get(url).json()
        name_set = {tag['name'] for tag in tags}
        if jina.__version__ in name_set:
            return jina.__version__
        else:
            return 'master'

    def _create_node(self, suffix):
        name = f'{self.name}_{suffix}' if suffix != '' else self.name
        dns_name = kubernetes_deployment.to_dns_name(name)
        return {
            'name': name,
            'head_host': f'{dns_name}.{self.args.k8s_namespace}.svc.cluster.local',
            'head_port_in': self.fixed_head_port_in,
            'tail_port_out': self.fixed_tail_port_out,
            'head_zmq_identity': self.head_zmq_identity,
        }

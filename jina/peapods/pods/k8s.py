import copy
import os
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
        replicas = getattr(args, 'replicas', 1)
        uses_before = getattr(args, 'uses_before', None)
        if parallel > 1 or (len(self.needs) > 1 and replicas > 1) or uses_before:
            # reasons to separate head and tail from peas is that they
            # can be deducted based on the previous and next pods
            parsed_args['head_deployment'] = copy.copy(args)
            parsed_args['head_deployment'].uses = (
                args.uses_before or __default_executor__
            )
        if parallel > 1 or getattr(args, 'uses_after', None):
            parsed_args['tail_deployment'] = copy.copy(args)
            parsed_args['tail_deployment'].uses = (
                args.uses_after or __default_executor__
            )

        parsed_args['deployments'] = [args] * parallel
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
        test_pip = os.getenv('JINA_K8S_USE_TEST_PIP') is not None
        image_name = (
            'jinaai/jina:test-pip'
            if test_pip
            else f'jinaai/jina:{self.version}-py38-standard'
        )
        kubernetes_deployment.deploy_service(
            self.name,
            namespace=self.args.k8s_namespace,
            image_name=image_name,
            container_cmd='["jina"]',
            container_args=f'["gateway", '
            f'"--grpc-data-requests", '
            f'{kubernetes_deployment.get_cli_params(self.args, ("pod_role",))}]',
            logger=JinaLogger(f'deploy_{self.name}'),
            replicas=1,
            pull_policy='IfNotPresent',
            port_expose=self.args.port_expose,
        )

    def _deploy_runtime(self, deployment_args, replicas, deployment_id):
        image_name = kubernetes_deployment.get_image_name(deployment_args.uses)
        name_suffix = self.name + (
            ''
            if self.args.parallel == 1 and type(deployment_id) == int
            else ('-' + str(deployment_id))
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
            test_pip = os.getenv('JINA_K8S_USE_TEST_PIP') is not None
            image_name = (
                'jinaai/jina:test-pip'
                if test_pip
                else f'jinaai/jina:{self.version}-py38-standard'
            )
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
            f'["executor", '
            f'"--native", '
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
        logger = JinaLogger(f'start_{self.name}')
        logger.info(
            f'🏝️\tCreate Namespace "{self.args.k8s_namespace}" for "{self.name}"'
        )
        kubernetes_tools.create(
            'namespace',
            {'name': self.args.k8s_namespace},
            logger=logger,
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

    def update_pea_args(self):
        """
        Regenerate deployment args
        """
        self.deployment_args = self._parse_args(self.args)

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
            'head_host': f'{dns_name}.{self.args.k8s_namespace}.svc',
            'head_port_in': self.fixed_head_port_in,
            'tail_port_out': self.fixed_tail_port_out,
            'head_zmq_identity': self.head_zmq_identity,
        }

    @property
    def _mermaid_str(self) -> List[str]:
        """String that will be used to represent the Pod graphically when `Flow.plot()` is invoked


        .. # noqa: DAR201
        """
        mermaid_graph = []
        if self.name != 'gateway':
            mermaid_graph = [f'subgraph {self.name};\n', f'direction LR;\n']

            num_replicas = getattr(self.args, 'replicas', 1)
            num_shards = getattr(self.args, 'parallel', 1)
            uses = self.args.uses
            if num_shards > 1:
                shard_names = [
                    f'{args.name}/shard-{i}'
                    for i, args in enumerate(self.deployment_args['deployments'])
                ]
                for shard_name in shard_names:
                    shard_mermaid_graph = [
                        f'subgraph {shard_name}\n',
                        f'direction TB;\n',
                    ]
                    for replica_id in range(num_replicas):
                        shard_mermaid_graph.append(
                            f'{shard_name}/replica-{replica_id}[{uses}]\n'
                        )
                    shard_mermaid_graph.append(f'end\n')
                    mermaid_graph.extend(shard_mermaid_graph)
                head_name = f'{self.name}/head'
                tail_name = f'{self.name}/tail'
                head_to_show = self.args.uses_before
                if head_to_show is None or head_to_show == __default_executor__:
                    head_to_show = head_name
                tail_to_show = self.args.uses_after
                if tail_to_show is None or tail_to_show == __default_executor__:
                    tail_to_show = tail_name
                if head_name:
                    for shard_name in shard_names:
                        mermaid_graph.append(
                            f'{head_name}[{head_to_show}]:::HEADTAIL --> {shard_name}[{uses}];'
                        )

                if tail_name:
                    for shard_name in shard_names:
                        mermaid_graph.append(
                            f'{shard_name}[{uses}] --> {tail_name}[{tail_to_show}]:::HEADTAIL;'
                        )
            else:
                for replica_id in range(num_replicas):
                    mermaid_graph.append(f'{self.name}/replica-{replica_id}[{uses}];')

            mermaid_graph.append(f'end;')
        return mermaid_graph

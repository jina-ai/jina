from argparse import Namespace
from typing import Optional, Dict, Union, Set, List

from .kubernetes import kubernetes_deployment

from ...logging.logger import JinaLogger
from .. import BasePod


class K8sPod(BasePod):
    def __init__(
        self, args: Union['Namespace', Dict], needs: Optional[Set[str]] = None
    ):
        super().__init__()
        self.args = args
        self.needs = needs or set()
        self.peas_args = self._parse_args(args)

    def _parse_args(
        self, args: Namespace
    ) -> Dict[str, Optional[Union[List[Namespace], Namespace]]]:
        return self._parse_base_pod_args(args)

    def _parse_base_pod_args(self, args):
        parsed_args = {'peas': []}
        parsed_args['peas'] = [args]
        # note that peas_args['peas'][0] exist either way and carries the original property
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

    def start(self) -> 'K8sPod':
        # kubernetes_tooks start things
        if self.name == 'gateway':
            kubernetes_deployment.deploy_service(
                self.name,
                namespace=self.args.k8s_namespace,  # maybe new args for kubernetes Pod
                port_in=self.args.port_in,
                port_out=self.args.port_out,
                port_ctrl=self.args.port_ctrl,
                port_expose=self.args.port_expose,
                image_name='jinaai/jina',
                container_cmd='["jina"]',
                container_args=f'["gateway", '
                f'{kubernetes_deployment.get_cli_params(self.args)}]',
                logger=JinaLogger(f'deploy_{self.name}'),
                replicas=1,
                init_container=None,
            )
        else:
            image_name = kubernetes_deployment.get_image_name(self.args.uses)
            pea_args = self.peas_args['peas'][0]
            # for now, no shards
            dns_name = kubernetes_deployment.to_dns_name(self.name)
            init_container_args = kubernetes_deployment.get_init_container_args(self)
            # we will see with shards
            uses_metas = kubernetes_deployment.dictionary_to_cli_param({'pea_id': 0})
            uses_with = kubernetes_deployment.dictionary_to_cli_param(
                self.args.uses_with
            )
            uses_with_string = f'"--uses-with", "{uses_with}", ' if uses_with else ''
            if image_name == 'BaseExecutor':
                image_name = 'jinaai/jina'
                container_args = (
                    f'["grpc_data_runtime", '
                    f'"--uses", "BaseExecutor", '
                    f'"--uses-metas", "{uses_metas}", '
                    + uses_with_string
                    + f'{kubernetes_deployment.get_cli_params(self.args)}]'
                )

            else:
                container_args = (
                    f'["grpc_data_runtime", '
                    f'"--uses", "config.yml", '
                    f'"--uses-metas", "{uses_metas}", '
                    + uses_with_string
                    + f'{kubernetes_deployment.get_cli_params(self.args)}]'
                )

            replicas = self.args.replicas
            kubernetes_deployment.deploy_service(
                dns_name,
                namespace=self.args.k8s_namespace,  # maybe new args for kubernetes Pod
                port_in=pea_args.port_in,
                port_out=pea_args.port_out,
                port_ctrl=pea_args.port_ctrl,
                port_expose=pea_args.port_expose,
                image_name=image_name,
                container_cmd='["jina"]',
                container_args=container_args,
                logger=JinaLogger(f'deploy_{self.name}'),
                replicas=replicas,
                init_container=init_container_args,
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

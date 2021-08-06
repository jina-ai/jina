from argparse import Namespace
from typing import Optional, Dict, Union, Set

from ...hubble.helper import parse_hub_uri
from ...hubble.hubio import HubIO
from .. import BasePod


class K8sPod(BasePod):
    def __init__(
        self, args: Union['Namespace', Dict], needs: Optional[Set[str]] = None
    ):
        super().__init__()
        args.upload_files = BasePod._set_upload_files(args)
        self.args = args
        self.needs = (
            needs or set()
        )  #: used in the :class:`jina.flow.Flow` to build the graph

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.join()

    def join(self):
        # potentially have some call to kubernetes_tools.destroy
        pass

    def is_singleton(self) -> bool:
        pass

    def start(self) -> 'K8sPod':
        """
        Start to run all :class:`Pod` and :class:`Pea` in this CompoundPod.

        :return: started CompoundPod

        .. note::
            If one of the :class:`Pod` fails to start, make sure that all of them
            are properly closed.
        """

        from .kubernetes import kubernetes_tools

        if self.name == 'gateway':
            print(f'🔒\tCreate "gateway service"')
            external_gateway_service = 'gateway-exposed'
            kubernetes_tools.create(
                'service',
                {
                    'name': external_gateway_service,
                    'target': 'gateway',
                    'namespace': 'jina-namespace',  # TODO: to check, how to pass
                    'port': 8080,
                    'type': 'ClusterIP',
                },
            )
            kubernetes_tools.create(
                'service',
                {
                    'name': 'gateway-in',
                    'target': 'gateway',
                    'namespace': 'jina-namespace',  # TODO: to check, how to pass
                    'port': 8081,
                    'type': 'ClusterIP',
                },
            )

            # gateway_cluster_ip = kubernetes_tools.get_service_cluster_ip(
            #     'gateway-in', namespace
            # )

            kubernetes_tools.create(
                'deployment',
                {
                    'name': 'gateway',
                    'replicas': 1,
                    'port': 8080,
                    'command': "[\"jina\"]",
                    'args': "[\"gateway\"]",  # TODO: add the correct parameters here (not fake yaml or Flow)
                    'image': 'jina-ai/jina',  # TODO: how to extract the proper jina image
                    'namespace': 'jina-namespace',
                },
            )
        else:
            scheme, name, tag, secret = parse_hub_uri(self.args.uses)
            meta_data = HubIO.fetch_meta(name)
            image_name = meta_data.image_name
            replicas = self.args.replicas
            print(
                f'🔋\tCreate Service for "{self.name}" with image "{name}" pulling from "{image_name}"'
            )
            kubernetes_tools.create(
                'service',
                {
                    'name': name.lower(),
                    'target': name.lower(),
                    'namespace': 'jina-namespace',  # TODO: to check, how to pass
                    'port': 8081,
                    'type': 'ClusterIP',
                },
            )
            print(f'🐳\tCreate Deployment for "{image_name}" with replicas {replicas}')
            kubernetes_tools.create(
                'deployment',
                {
                    'name': name.lower(),
                    'namespace': 'jina-namespace',  # TODO: to check, how to pass
                    'image': image_name,
                    'replicas': replicas,
                    'command': "[\"jina\"]",
                    'args': "[\"executor\", \"--uses\", \"config.yml\", \"--port-in\", \"8081\", \"--dynamic-routing-in\", \"--dynamic-routing-out\", \"--socket-in\", \"ROUTER_BIND\", \"--socket-out\", \"ROUTER_BIND\"]",
                    'port': 8081,
                },
            )

    def wait_start_success(self) -> None:
        pass

    @property
    def is_ready(self) -> bool:
        """
        Checks if Pod is ready.
        :return: true if the peas and pods are ready to serve requests

        .. note::
            A Pod is ready when all the Peas it contains are ready
        """
        return True

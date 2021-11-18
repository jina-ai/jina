from argparse import Namespace
from typing import Optional, Set

from .k8s import K8sPod
from .. import BasePod
from .. import Pod
from ...enums import InfrastructureType


class PodFactory:
    """
    A PodFactory is a factory class, abstracting the Pod creation
    """

    @staticmethod
    def build_pod(
        args: 'Namespace',
        needs: Optional[Set[str]] = None,
        infrastructure: InfrastructureType = InfrastructureType.JINA,
    ) -> BasePod:
        """Build an implementation of a `BasePod` interface

        :param args: pod arguments parsed from the CLI.
        :param needs: pod names of preceding pods
        :param infrastructure: infrastructure where the flow should run

        :return: the created BasePod
        """
        if infrastructure == InfrastructureType.K8S:
            return K8sPod(args, needs=needs)
        else:
            return Pod(args, needs=needs)

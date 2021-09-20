from argparse import Namespace
from typing import Optional, Set

from ...enums import InfrastructureType
from .compound import CompoundPod
from .. import BasePod
from .. import Pod
from .k8s import K8sPod


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
        elif getattr(args, 'replicas', 1) > 1:
            return CompoundPod(args, needs=needs)
        else:
            return Pod(args, needs=needs)

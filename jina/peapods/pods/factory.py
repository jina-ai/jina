from argparse import Namespace
from typing import Optional, Set

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
        args: 'Namespace', needs: Optional[Set[str]] = None, k8s: bool = False
    ) -> BasePod:
        """Build an implementation of a `BasePod` interface

        :param args: pod arguments parsed from the CLI.
        :param needs: pod names of preceding pods

        :return: the created BasePod
        """
        if k8s:
            return K8sPod(args, needs=needs)
        if getattr(args, 'replicas', 1) > 1:
            return CompoundPod(args, needs=needs)
        else:
            return Pod(args, needs=needs)

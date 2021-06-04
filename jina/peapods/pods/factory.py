from argparse import Namespace
from typing import Optional, Set

from .compound import CompoundPod
from .. import BasePod
from .. import Pod


class PodFactory:
    """
    A PodFactory is a factory class, abstracting the Pod creation
    """

    @staticmethod
    def build_pod(
        args: 'Namespace',
        needs: Optional[Set[str]] = None,
        flow_identity: Optional[str] = None,
    ) -> BasePod:
        """Build an implementation of a `BasePod` interface

        :param args: pod arguments parsed from the CLI.
        :param needs: pod names of preceding pods
        :param flow_identity: the identity of the Flow this Pod belongs to if it does belong to a Flow

        :return: the created BasePod
        """
        args.flow_identity = flow_identity
        if getattr(args, 'replicas', 1) > 1:
            return CompoundPod(args, needs=needs)
        else:
            return Pod(args, needs=needs)

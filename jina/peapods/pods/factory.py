from typing import Union, Optional, Dict, Set
from argparse import Namespace

from .. import Pod
from .. import BasePod
from .compoundpod import CompoundPod


class PodFactory:
    """
    A PodFactory is a factory class, abstracting the Pod creation
    """

    @staticmethod
    def build_pod(
        args: Union['Namespace', Dict], needs: Optional[Set[str]] = None
    ) -> BasePod:
        """Build an implementation of a `BasePod` interface

        :param args: pod arguments parsed from the CLI.
        :param needs: pod names of preceding pods

        :return: the created BasePod
        """
        if args.replicas > 1:
            return CompoundPod(args, needs=needs)
        else:
            return Pod(args, needs=needs)

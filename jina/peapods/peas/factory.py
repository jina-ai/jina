from argparse import Namespace
from copy import deepcopy

from . import BasePea, Pea
from .container import ContainerPea

from ...hubble.helper import is_valid_huburi
from ...hubble.hubio import HubIO


class PeaFactory:
    """
    A PeaFactory is a factory class, abstracting the Pea creation
    """

    @staticmethod
    def build_pea(
        args: 'Namespace',
    ) -> BasePea:
        """Build an implementation of a `BasePea` interface

        :param args: pod arguments parsed from the CLI.

        :return: the created BasePod
        """
        # copy to update but forward original
        cargs = deepcopy(args)
        if is_valid_huburi(cargs.uses):
            _hub_args = deepcopy(args)
            _hub_args.uri = args.uses
            _hub_args.no_usage = True
            cargs.uses = HubIO(_hub_args).pull()

        if cargs.uses and cargs.uses.startswith('docker://'):
            return ContainerPea(args)
        else:
            return Pea(args)

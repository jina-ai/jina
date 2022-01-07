from argparse import Namespace
from copy import deepcopy
from typing import TYPE_CHECKING, Type

from ... import __default_host__
from . import Pea
from .jinad import JinaDPea
from .container import ContainerPea
from ...enums import PeaRoleType

from ...hubble.helper import is_valid_huburi
from ...hubble.hubio import HubIO

if TYPE_CHECKING:
    from . import BasePea


class PeaFactory:
    """
    A PeaFactory is a factory class, abstracting the Pea creation
    """

    @staticmethod
    def build_pea(args: 'Namespace') -> Type['BasePea']:
        """Build an implementation of a `BasePea` interface

        :param args: pod arguments parsed from the CLI.

        :return: the created BasePod
        """
        # copy to update but forward original
        cargs = deepcopy(args)
        if cargs.host != __default_host__ and not cargs.disable_remote:
            cargs.timeout_ready = -1
            return JinaDPea(cargs)

        if is_valid_huburi(cargs.uses):
            _hub_args = deepcopy(args)
            _hub_args.uri = args.uses
            _hub_args.no_usage = True
            cargs.uses = HubIO(_hub_args).pull()

        if (
            cargs.pea_role != PeaRoleType.HEAD
            and cargs.uses
            and cargs.uses.startswith('docker://')
        ):
            return ContainerPea(cargs)
        else:
            return Pea(args)

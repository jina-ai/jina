from argparse import Namespace
from copy import deepcopy
from typing import TYPE_CHECKING, Type

from jina import __default_host__
from jina.enums import PodRoleType
from jina.hubble.helper import is_valid_huburi
from jina.hubble.hubio import HubIO
from jina.orchestrate.pods import Pod
from jina.orchestrate.pods.container import ContainerPod
from jina.orchestrate.pods.jinad import JinaDPod

if TYPE_CHECKING:
    from jina.orchestrate.pods import BasePod


class PodFactory:
    """
    A PodFactory is a factory class, abstracting the Pod creation
    """

    @staticmethod
    def build_pod(args: 'Namespace') -> Type['BasePod']:
        """Build an implementation of a `BasePod` interface

        :param args: deployment arguments parsed from the CLI.

        :return: the created BaseDeployment
        """
        # copy to update but forward original
        cargs = deepcopy(args)
        if cargs.host != __default_host__:
            cargs.timeout_ready = -1
            return JinaDPod(cargs)

        if is_valid_huburi(cargs.uses):
            _hub_args = deepcopy(args)
            _hub_args.uri = args.uses
            _hub_args.no_usage = True
            cargs.uses = HubIO(_hub_args).pull()

        if (
            cargs.pod_role != PodRoleType.HEAD
            and cargs.uses
            and cargs.uses.startswith('docker://')
        ):
            return ContainerPod(cargs)
        else:
            return Pod(args)

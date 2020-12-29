import argparse

from .base import BasePea
from ..runtimes.asyncio.grpc import GRPCRuntime
from ..runtimes.asyncio.rest import RESTRuntime
from ..runtimes.container import ContainerRuntime
from ..runtimes.jinad import JinadRuntime
from ..runtimes.ssh import SSHRuntime
from ..runtimes.zmq.zed import ZEDRuntime


class GRPCGatewayPea(BasePea):
    runtime_cls = GRPCRuntime


class RESTGatewayPea(BasePea):
    runtime_cls = RESTRuntime


class ZEDPea(BasePea):
    runtime_cls = ZEDRuntime


class ContainerPea(BasePea):
    runtime_cls = ContainerRuntime


class JinadPea(BasePea):
    runtime_cls = JinadRuntime


class SSHPea(BasePea):
    runtime_cls = SSHRuntime


class Pea(BasePea):

    def __init__(self, args: 'argparse.Namespace'):
        self.runtime_cls = args.runtime_cls
        super().__init__(args)

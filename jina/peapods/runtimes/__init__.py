from .asyncio.grpc import GRPCRuntime
from .asyncio.rest import RESTRuntime
from .container import ContainerRuntime
from .jinad import JinadRuntime
from .ssh import SSHRuntime
from .zmq.zed import ZEDRuntime


def list_all_runtimes():
    """List all public runtimes that can be used directly with :class:`jina.peapods.peas.BasePea`"""
    from ...peapods.runtimes.base import BaseRuntime

    return [
        k
        for k, s in globals().items()
        if isinstance(s, type) and issubclass(s, BaseRuntime)
    ]


def get_runtime(name: str):
    """Get a public runtime by its name"""
    from ...peapods.runtimes.base import BaseRuntime

    s = globals()[name]
    if isinstance(s, type) and issubclass(s, BaseRuntime):
        return s
    else:
        raise TypeError(f'{s!r} is not in type {BaseRuntime!r}')

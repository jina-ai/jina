def list_all_runtimes():
    """List all public runtimes that can be used directly with :class:`jina.peapods.peas.BasePea`

    # noqa: DAR101
    # noqa: DAR201
    """
    from ...peapods.runtimes.base import BaseRuntime
    from .gateway.grpc import GRPCRuntime
    from .gateway.http import HTTPRuntime
    from .gateway.websocket import WebSocketRuntime
    from .container import ContainerRuntime
    from .jinad import JinadRuntime
    from .zmq.zed import ZEDRuntime
    from .grpc import GRPCDataRuntime

    return [
        k
        for k, s in locals().items()
        if isinstance(s, type) and issubclass(s, BaseRuntime)
    ]


def get_runtime(name: str):
    """Get a public runtime by its name

    # noqa: DAR101
    # noqa: DAR201
    """
    from ...peapods.runtimes.base import BaseRuntime
    from .gateway.grpc import GRPCRuntime
    from .gateway.http import HTTPRuntime
    from .gateway.websocket import WebSocketRuntime
    from .container import ContainerRuntime
    from .jinad import JinadRuntime
    from .zmq.zed import ZEDRuntime
    from .grpc import GRPCDataRuntime

    s = locals()[name]
    if isinstance(s, type) and issubclass(s, BaseRuntime):
        return s
    else:
        raise TypeError(f'{s!r} is not in type {BaseRuntime!r}')

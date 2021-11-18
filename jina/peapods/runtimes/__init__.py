def list_all_runtimes():
    """List all public runtimes that can be used directly with :class:`jina.peapods.peas.Pea`

    # noqa: DAR101
    # noqa: DAR201
    """
    from ...peapods.runtimes.base import BaseRuntime
    from .gateway.grpc import GRPCGatewayRuntime
    from .gateway.http import HTTPGatewayRuntime
    from .gateway.websocket import WebSocketGatewayRuntime
    from .worker import WorkerRuntime

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
    from .gateway.grpc import GRPCGatewayRuntime
    from .gateway.http import HTTPGatewayRuntime
    from .gateway.websocket import WebSocketGatewayRuntime
    from .worker import WorkerRuntime
    from .head import HeadRuntime

    s = locals()[name]
    if isinstance(s, type) and issubclass(s, BaseRuntime):
        return s
    else:
        raise TypeError(f'{s!r} is not in type {BaseRuntime!r}')

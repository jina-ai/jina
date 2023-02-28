def get_runtime(name: str):
    """Get a public runtime by its name

    # noqa: DAR101
    # noqa: DAR201
    """
    from jina.serve.runtimes.base import BaseRuntime
    from jina.serve.runtimes.gateway import GatewayRuntime
    from jina.serve.runtimes.head.grpc import HeadRuntime
    from jina.serve.runtimes.worker.grpc import WorkerRuntime

    s = locals()[name]
    if isinstance(s, type) and issubclass(s, BaseRuntime):
        return s
    else:
        raise TypeError(f'{s!r} is not in type {BaseRuntime!r}')

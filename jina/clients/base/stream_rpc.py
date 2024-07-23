from jina.clients.helper import callback_exec
from jina.proto import jina_pb2_grpc


class StreamRpc:
    """Class that encapsulated the methods required to run a stream rpc call from the client. Instantiate a single class
    for each client request.
    """

    def __init__(
        self,
        channel,
        continue_on_error,
        metadata,
        on_always,
        on_done,
        on_error,
        p_bar,
        req_iter,
        max_attempts,
        backoff_multiplier,
        initial_backoff,
        max_backoff,
        logger,
        show_progress,
        compression,
        **kwargs
    ):
        self.compression = compression
        self.show_progress = show_progress
        self.logger = logger
        self.max_backoff = max_backoff
        self.initial_backoff = initial_backoff
        self.backoff_multiplier = backoff_multiplier
        self.max_attempts = max_attempts
        self.req_iter = req_iter
        self.p_bar = p_bar
        self.on_error = on_error
        self.on_done = on_done
        self.on_always = on_always
        self.metadata = metadata
        self.continue_on_error = continue_on_error
        self.channel = channel
        self.kwargs = kwargs

    async def stream_rpc_with_retry(self):
        """Wraps the stream rpc logic with retry loop based on the retry params.
        :yields: Responses received from the target.
        """
        stub = jina_pb2_grpc.JinaRPCStub(self.channel)
        async for resp in stub.Call(
            self.req_iter,
            compression=self.compression,
            metadata=self.metadata,
            credentials=self.kwargs.get('credentials', None),
            timeout=self.kwargs.get('timeout', None),
        ):
            callback_exec(
                response=resp,
                logger=self.logger,
                docs=None,
                on_error=self.on_error,
                on_done=self.on_done,
                on_always=self.on_always,
                continue_on_error=self.continue_on_error,
            )
            if self.show_progress:
                self.p_bar.update()
            yield resp

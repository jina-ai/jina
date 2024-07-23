import asyncio
from typing import TYPE_CHECKING, Optional, Tuple

import grpc

from jina.clients.base.retry import wait_or_raise_err
from jina.clients.helper import callback_exec
from jina.excepts import InternalNetworkError
from jina.proto import jina_pb2_grpc
from jina.serve.stream import RequestStreamer

if TYPE_CHECKING:
    from jina.types.request import Request


class UnaryRpc:
    """Class that encapsulated the methods required to run unary rpc calls from the client. Instantiate a single class
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
        client_args,
        prefetch,
        results_in_order,
        **kwargs
    ):
        self.results_in_order = results_in_order
        self.prefetch = prefetch
        self.client_args = client_args
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

    async def unary_rpc_with_retry(self):
        """Wraps the unary rpc call with retry loop based on the retry params.
        :yields: Responses received from the target.
        """
        stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(self.channel)

        def _request_handler(
            request: 'Request', **kwargs
        ) -> 'Tuple[asyncio.Future, Optional[asyncio.Future]]':
            async def _with_retry(req: 'Request'):
                for attempt in range(1, self.max_attempts + 1):
                    try:
                        return await stub.process_single_data(
                            req,
                            compression=self.compression,
                            metadata=self.metadata,
                            credentials=self.kwargs.get('credentials', None),
                            timeout=self.kwargs.get('timeout', None),
                        )
                    except (
                        grpc.aio.AioRpcError,
                        InternalNetworkError,
                    ) as err:
                        await wait_or_raise_err(
                            attempt=attempt,
                            err=err,
                            max_attempts=self.max_attempts,
                            backoff_multiplier=self.backoff_multiplier,
                            initial_backoff=self.initial_backoff,
                            max_backoff=self.max_backoff,
                        )

            return (
                asyncio.ensure_future(_with_retry(request)),
                None,
            )

        def _result_handler(resp):
            callback_exec(
                response=resp,
                logger=self.logger,
                docs=None,
                on_error=self.on_error,
                on_done=self.on_done,
                on_always=self.on_always,
                continue_on_error=self.continue_on_error,
            )
            return resp

        streamer_args = vars(self.client_args)
        if self.prefetch:
            streamer_args['prefetch'] = self.prefetch
        streamer = RequestStreamer(
            request_handler=_request_handler,
            result_handler=_result_handler,
            iterate_sync_in_thread=False,
            logger=self.logger,
            **streamer_args,
        )
        async for response in streamer.stream(
            request_iterator=self.req_iter, results_in_order=self.results_in_order
        ):
            if self.show_progress:
                self.p_bar.update()
            yield response

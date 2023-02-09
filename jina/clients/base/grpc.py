import asyncio
import json
import threading
from typing import TYPE_CHECKING, Optional, Tuple

import grpc
from grpc import RpcError

from jina.clients.base import BaseClient
from jina.clients.helper import callback_exec
from jina.excepts import BadClientInput, BadServerFlow, InternalNetworkError
from jina.logging.profile import ProgressBar
from jina.proto import jina_pb2, jina_pb2_grpc
from jina.serve.helper import extract_trailing_metadata
from jina.serve.networking.utils import get_default_grpc_options, get_grpc_channel
from jina.serve.stream import RequestStreamer
from jina.types.request.data import Request

if TYPE_CHECKING:  # pragma: no cover
    from jina.clients.base import CallbackFnType, InputType


class GRPCBaseClient(BaseClient):
    """A simple Python client for connecting to the gRPC gateway.

    It manages the asyncio event loop internally, so all interfaces are synchronous from the outside.
    """

    _lock = threading.RLock()

    async def _is_flow_ready(self, **kwargs) -> bool:
        """Sends a dry run to the Flow to validate if the Flow is ready to receive requests

        :param kwargs: potential kwargs received passed from the public interface
        :return: boolean indicating the health/readiness of the Flow
        """
        try:
            async with get_grpc_channel(
                f'{self.args.host}:{self.args.port}',
                asyncio=True,
                tls=self.args.tls,
            ) as channel:
                stub = jina_pb2_grpc.JinaGatewayDryRunRPCStub(channel)
                self.logger.debug(f'connected to {self.args.host}:{self.args.port}')
                call_result = stub.dry_run(
                    jina_pb2.google_dot_protobuf_dot_empty__pb2.Empty(),
                    metadata=kwargs.get('metadata', None),
                    credentials=kwargs.get('credentials', None),
                    timeout=kwargs.get('timeout', None),
                )
                metadata, response = (
                    await call_result.trailing_metadata(),
                    await call_result,
                )
                if response.code == jina_pb2.StatusProto.SUCCESS:
                    return True
                else:
                    self.logger.error(
                        f'Returned code is not expected! Exception: {response.exception}'
                    )
        except RpcError as e:
            self.logger.error(f'RpcError: {e.details()}')
        except Exception as e:
            self.logger.error(f'Error while getting response from grpc server {e!r}')

        return False

    async def _stream_rpc(
        self,
        channel,
        req_iter,
        metadata,
        on_error,
        on_done,
        on_always,
        continue_on_error,
        p_bar,
        **kwargs,
    ):
        stub = jina_pb2_grpc.JinaRPCStub(channel)
        async for resp in stub.Call(
            req_iter,
            compression=self.compression,
            metadata=metadata,
            credentials=kwargs.get('credentials', None),
            timeout=kwargs.get('timeout', None),
        ):
            callback_exec(
                response=resp,
                on_error=on_error,
                on_done=on_done,
                on_always=on_always,
                continue_on_error=continue_on_error,
                logger=self.logger,
            )
            if self.show_progress:
                p_bar.update()
            yield resp

    async def _unary_rpc(
        self,
        channel,
        req_iter,
        metadata,
        on_error,
        on_done,
        on_always,
        continue_on_error,
        p_bar,
        results_in_order,
        prefetch,
        **kwargs,
    ):
        stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)

        def _request_handler(
            request: 'Request',
        ) -> 'Tuple[asyncio.Future, Optional[asyncio.Future]]':
            return (
                asyncio.ensure_future(
                    stub.process_single_data(
                        request,
                        compression=self.compression,
                        metadata=metadata,
                        credentials=kwargs.get('credentials', None),
                        timeout=kwargs.get('timeout', None),
                    )
                ),
                None,
            )

        def _result_handler(resp):
            callback_exec(
                response=resp,
                on_error=on_error,
                on_done=on_done,
                on_always=on_always,
                continue_on_error=continue_on_error,
                logger=self.logger,
            )
            return resp

        streamer_args = vars(self.args)
        if prefetch:
            streamer_args['prefetch'] = prefetch
        streamer = RequestStreamer(
            request_handler=_request_handler,
            result_handler=_result_handler,
            iterate_sync_in_thread=False,
            logger=self.logger,
            **streamer_args,
        )
        async for response in streamer.stream(
            request_iterator=req_iter, results_in_order=results_in_order
        ):
            if self.show_progress:
                p_bar.update()
            yield response

    async def _get_results(
        self,
        inputs: 'InputType',
        on_done: 'CallbackFnType',
        on_error: Optional['CallbackFnType'] = None,
        on_always: Optional['CallbackFnType'] = None,
        compression: Optional[str] = None,
        max_attempts: int = 1,
        initial_backoff: float = 0.5,
        max_backoff: float = 0.1,
        backoff_multiplier: float = 1.5,
        results_in_order: bool = False,
        stream: bool = True,
        prefetch: Optional[int] = None,
        **kwargs,
    ):
        try:
            self.compression = (
                getattr(grpc.Compression, compression)
                if compression
                else grpc.Compression.NoCompression
            )

            self.inputs = inputs
            req_iter = self._get_requests(**kwargs)
            continue_on_error = self.continue_on_error
            # while loop with retries, check in which state the `iterator` remains after failure
            options = get_default_grpc_options()
            if max_attempts > 1:
                service_config_json = json.dumps(
                    {
                        "methodConfig": [
                            {
                                # To apply retry to all methods, put [{}] in the "name" field
                                "name": [{}],
                                "retryPolicy": {
                                    "maxAttempts": max_attempts,
                                    "initialBackoff": f"{initial_backoff}s",
                                    "maxBackoff": f"{max_backoff}s",
                                    "backoffMultiplier": backoff_multiplier,
                                    "retryableStatusCodes": [
                                        "UNAVAILABLE",
                                        "DEADLINE_EXCEEDED",
                                        "INTERNAL",
                                    ],
                                },
                            }
                        ]
                    }
                )
                # NOTE: the retry feature will be enabled by default >=v1.40.0
                options.append(("grpc.enable_retries", 1))
                options.append(("grpc.service_config", service_config_json))

            metadata = kwargs.pop('metadata', ())
            if results_in_order:
                metadata = metadata + (('__results_in_order__', 'true'),)

            if prefetch:
                metadata = metadata + (('__prefetch__', str(prefetch)),)

            with self._lock:
                async with get_grpc_channel(
                    f'{self.args.host}:{self.args.port}',
                    options=options,
                    asyncio=True,
                    tls=self.args.tls,
                    aio_tracing_client_interceptors=self.aio_tracing_client_interceptors(),
                ) as channel:
                    self.logger.debug(f'connected to {self.args.host}:{self.args.port}')

                    with ProgressBar(
                        total_length=self._inputs_length, disable=not self.show_progress
                    ) as p_bar:
                        try:
                            if stream:
                                async for resp in self._stream_rpc(
                                    channel=channel,
                                    req_iter=req_iter,
                                    metadata=metadata,
                                    on_error=on_error,
                                    on_done=on_done,
                                    on_always=on_always,
                                    continue_on_error=continue_on_error,
                                    p_bar=p_bar,
                                    **kwargs,
                                ):
                                    yield resp
                            else:
                                async for resp in self._unary_rpc(
                                    channel=channel,
                                    req_iter=req_iter,
                                    metadata=metadata,
                                    on_error=on_error,
                                    on_done=on_done,
                                    on_always=on_always,
                                    continue_on_error=continue_on_error,
                                    p_bar=p_bar,
                                    results_in_order=results_in_order,
                                    prefetch=prefetch,
                                    **kwargs,
                                ):
                                    yield resp

                        except (
                            grpc.aio._call.AioRpcError,
                            InternalNetworkError,
                        ) as err:
                            my_code = err.code()
                            my_details = err.details()
                            trailing_metadata = extract_trailing_metadata(err)
                            msg = f'gRPC error: {my_code} {my_details}'
                            if trailing_metadata:
                                msg = f'gRPC error: {my_code} {my_details}\n{trailing_metadata}'

                            if my_code == grpc.StatusCode.UNAVAILABLE:
                                self.logger.error(
                                    f'{msg}\nThe ongoing request is terminated as the server is not available or closed already.'
                                )
                                raise ConnectionError(my_details)
                            if my_code == grpc.StatusCode.NOT_FOUND:
                                self.logger.error(
                                    f'{msg}\nThe ongoing request is terminated as a resource cannot be found.'
                                )
                                raise ConnectionError(my_details)
                            elif my_code == grpc.StatusCode.DEADLINE_EXCEEDED:
                                self.logger.error(
                                    f'{msg}\nThe ongoing request is terminated due to a server-side timeout.'
                                )
                                raise ConnectionError(my_details)
                            elif my_code == grpc.StatusCode.INTERNAL:
                                self.logger.error(
                                    f'{msg}\ninternal error on the server side'
                                )
                                raise err
                            elif (
                                my_code == grpc.StatusCode.UNKNOWN
                                and 'asyncio.exceptions.TimeoutError' in my_details
                            ):
                                raise BadClientInput(
                                    f'{msg}\n'
                                    'often the case is that you define/send a bad input iterator to jina, '
                                    'please double check your input iterator'
                                ) from err
                            else:
                                raise BadServerFlow(msg) from err

        except KeyboardInterrupt:
            self.logger.warning('user cancel the process')
        except asyncio.CancelledError as ex:
            self.logger.warning(f'process error: {ex!r}')
            raise
        except:
            # Not sure why, adding this line helps in fixing a hanging test
            raise

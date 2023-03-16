import asyncio
import threading
from typing import TYPE_CHECKING, Optional

import grpc
from grpc import RpcError

from jina.clients.base import BaseClient
from jina.clients.base.helper import client_grpc_options
from jina.clients.base.stream_rpc import StreamRpc
from jina.clients.base.unary_rpc import UnaryRpc
from jina.excepts import BadClientInput, BadServerFlow, InternalNetworkError
from jina.logging.profile import ProgressBar
from jina.proto import jina_pb2, jina_pb2_grpc
from jina.serve.helper import extract_trailing_metadata
from jina.serve.networking.utils import get_grpc_channel

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

    async def _get_results(
        self,
        inputs: 'InputType',
        on_done: 'CallbackFnType',
        on_error: Optional['CallbackFnType'] = None,
        on_always: Optional['CallbackFnType'] = None,
        compression: Optional[str] = None,
        max_attempts: int = 1,
        initial_backoff: float = 0.5,
        max_backoff: float = 2,
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
            options = client_grpc_options(
                backoff_multiplier,
                initial_backoff,
                max_attempts,
                max_backoff,
                self.args.grpc_channel_options,
            )

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
                                stream_rpc = StreamRpc(
                                    channel=channel,
                                    continue_on_error=continue_on_error,
                                    metadata=metadata,
                                    on_always=on_always,
                                    on_done=on_done,
                                    on_error=on_error,
                                    p_bar=p_bar,
                                    req_iter=req_iter,
                                    max_attempts=max_attempts,
                                    backoff_multiplier=backoff_multiplier,
                                    initial_backoff=initial_backoff,
                                    max_backoff=max_backoff,
                                    logger=self.logger,
                                    show_progress=self.show_progress,
                                    compression=self.compression,
                                    **kwargs,
                                )
                                async for response in stream_rpc.stream_rpc_with_retry():
                                    yield response
                            else:
                                unary_rpc = UnaryRpc(
                                    channel=channel,
                                    continue_on_error=continue_on_error,
                                    metadata=metadata,
                                    on_always=on_always,
                                    on_done=on_done,
                                    on_error=on_error,
                                    p_bar=p_bar,
                                    req_iter=req_iter,
                                    max_attempts=max_attempts,
                                    backoff_multiplier=backoff_multiplier,
                                    initial_backoff=initial_backoff,
                                    max_backoff=max_backoff,
                                    logger=self.logger,
                                    show_progress=self.show_progress,
                                    compression=self.compression,
                                    client_args=self.args,
                                    prefetch=prefetch,
                                    results_in_order=results_in_order,
                                    **kwargs,
                                )
                                async for response in unary_rpc.unary_rpc_with_retry():
                                    yield response
                        except (grpc.aio.AioRpcError, InternalNetworkError) as err:
                            await self._handle_error_and_metadata(err)
        except KeyboardInterrupt:
            self.logger.warning('user cancel the process')
        except asyncio.CancelledError as ex:
            self.logger.warning(f'process error: {ex!r}')
            raise
        except:
            # Not sure why, adding this line helps in fixing a hanging test
            raise

    async def _handle_error_and_metadata(self, err):
        my_code = err.code()
        my_details = err.details()
        trailing_metadata = extract_trailing_metadata(err)
        msg = f'gRPC error: {my_code} {my_details}\n{trailing_metadata}'
        if my_code == grpc.StatusCode.UNAVAILABLE:
            self.logger.error(
                f'{msg}\nThe ongoing request is terminated as the server is not available or closed already.'
            )
            raise ConnectionError(msg)
        if my_code == grpc.StatusCode.NOT_FOUND:
            self.logger.error(
                f'{msg}\nThe ongoing request is terminated as a resource cannot be found.'
            )
            raise ConnectionError(msg)
        elif my_code == grpc.StatusCode.DEADLINE_EXCEEDED:
            self.logger.error(
                f'{msg}\nThe ongoing request is terminated due to a server-side timeout.'
            )
            raise ConnectionError(msg)
        elif my_code == grpc.StatusCode.INTERNAL:
            self.logger.error(f'{msg}\ninternal error on the server side')
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

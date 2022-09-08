import asyncio
from typing import TYPE_CHECKING, Optional

import grpc

from jina.clients.base import BaseClient
from jina.clients.helper import callback_exec
from jina.excepts import BadClientInput, BadServerFlow, InternalNetworkError
from jina.logging.profile import ProgressBar
from jina.proto import jina_pb2, jina_pb2_grpc
from jina.serve.networking import GrpcConnectionPool

if TYPE_CHECKING:
    from jina.clients.base import CallbackFnType, InputType


class GRPCBaseClient(BaseClient):
    """A simple Python client for connecting to the gRPC gateway.

    It manages the asyncio event loop internally, so all interfaces are synchronous from the outside.
    """

    async def _is_flow_ready(self, **kwargs) -> bool:
        """Sends a dry run to the Flow to validate if the Flow is ready to receive requests

        :param kwargs: potential kwargs received passed from the public interface
        :return: boolean indicating the health/readiness of the Flow
        """
        try:
            async with GrpcConnectionPool.get_grpc_channel(
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
            async with GrpcConnectionPool.get_grpc_channel(
                f'{self.args.host}:{self.args.port}',
                asyncio=True,
                tls=self.args.tls,
            ) as channel:
                stub = jina_pb2_grpc.JinaRPCStub(channel)
                self.logger.debug(f'connected to {self.args.host}:{self.args.port}')

                with ProgressBar(
                    total_length=self._inputs_length, disable=not self.show_progress
                ) as p_bar:
                    async for resp in stub.Call(
                        req_iter,
                        compression=self.compression,
                        metadata=kwargs.get('metadata', None),
                        credentials=kwargs.get('credentials', None),
                        timeout=kwargs.get('timeout', None),
                    ):
                        callback_exec(
                            response=resp,
                            on_error=on_error,
                            on_done=on_done,
                            on_always=on_always,
                            continue_on_error=self.continue_on_error,
                            logger=self.logger,
                        )
                        if self.show_progress:
                            p_bar.update()
                        yield resp

        except KeyboardInterrupt:
            self.logger.warning('user cancel the process')
        except asyncio.CancelledError as ex:
            self.logger.warning(f'process error: {ex!r}')
        except (grpc.aio._call.AioRpcError, InternalNetworkError) as err:
            my_code = err.code()
            my_details = err.details()
            msg = f'gRPC error: {my_code} {my_details}'

            if my_code == grpc.StatusCode.UNAVAILABLE:
                self.logger.error(
                    f'{msg}\nThe ongoing request is terminated as the server is not available or closed already.'
                )
                raise ConnectionError(my_details) from None
            elif my_code == grpc.StatusCode.DEADLINE_EXCEEDED:
                self.logger.error(
                    f'{msg}\nThe ongoing request is terminated due to a server-side timeout.'
                )
                raise ConnectionError(my_details) from None
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
        except:
            # Not sure why, adding this line helps in fixing a hanging test
            raise

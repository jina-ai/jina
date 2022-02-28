import asyncio
from contextlib import nullcontext
from typing import TYPE_CHECKING, Optional

import grpc

from jina.clients.base import BaseClient
from jina.clients.helper import callback_exec, callback_exec_on_error
from jina.excepts import BadClient, BadClientInput, BaseJinaException
from jina.logging.profile import ProgressBar
from jina.proto import jina_pb2_grpc
from jina.serve.networking import GrpcConnectionPool

if TYPE_CHECKING:
    from jina.clients.base import InputType, CallbackFnType


class GRPCBaseClient(BaseClient):
    """A simple Python client for connecting to the gRPC gateway.

    It manages the asyncio event loop internally, so all interfaces are synchronous from the outside.
    """

    async def _get_results(
        self,
        inputs: 'InputType',
        on_done: 'CallbackFnType',
        on_error: Optional['CallbackFnType'] = None,
        on_always: Optional['CallbackFnType'] = None,
        **kwargs,
    ):
        try:
            self.inputs = inputs
            req_iter = self._get_requests(**kwargs)
            async with GrpcConnectionPool.get_grpc_channel(
                f'{self.args.host}:{self.args.port}',
                asyncio=True,
                https=self.args.https,
            ) as channel:
                stub = jina_pb2_grpc.JinaRPCStub(channel)
                self.logger.debug(f'connected to {self.args.host}:{self.args.port}')

                cm1 = (
                    ProgressBar(total_length=self._inputs_length)
                    if self.show_progress
                    else nullcontext()
                )

                with cm1 as p_bar:
                    async for resp in stub.Call(req_iter):
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
        except grpc.aio._call.AioRpcError as rpc_ex:
            # Since this object is guaranteed to be a grpc.Call, might as well include that in its name.
            my_code = rpc_ex.code()
            my_details = rpc_ex.details()
            msg = f'gRPC error: {my_code} {my_details}'

            try:
                if my_code == grpc.StatusCode.UNAVAILABLE:
                    self.logger.error(
                        f'{msg}\nthe ongoing request is terminated as the server is not available or closed already'
                    )
                    raise rpc_ex
                elif my_code == grpc.StatusCode.INTERNAL:
                    self.logger.error(f'{msg}\ninternal error on the server side')
                    raise rpc_ex
                elif (
                    my_code == grpc.StatusCode.UNKNOWN
                    and 'asyncio.exceptions.TimeoutError' in my_details
                ):
                    raise BadClientInput(
                        f'{msg}\n'
                        'often the case is that you define/send a bad input iterator to jina, '
                        'please double check your input iterator'
                    ) from rpc_ex
                else:
                    raise BadClient(msg) from rpc_ex

            except (
                grpc.aio._call.AioRpcError,
                BaseJinaException,
            ) as e:  # depending on if there are callbacks we catch or not the exception
                if on_error or on_always:
                    if on_error:
                        callback_exec_on_error(on_error, e, self.logger)
                    if on_always:
                        callback_exec(
                            response=None,
                            on_error=None,
                            on_done=None,
                            on_always=on_always,
                            continue_on_error=self.continue_on_error,
                            logger=self.logger,
                        )
                else:
                    raise e

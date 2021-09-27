import asyncio
from contextlib import nullcontext
from typing import Callable, Union, Optional

import grpc

from ..base import BaseClient
from ..helper import callback_exec
from ..request import GeneratorSourceType
from ...excepts import BadClient, BadClientInput
from ...logging.profile import ProgressBar
from ...proto import jina_pb2_grpc
from ...types.request import Response

InputType = Union[GeneratorSourceType, Callable[..., GeneratorSourceType]]
CallbackFnType = Optional[Callable[[Response], None]]


class GRPCBaseClient(BaseClient):
    """A simple Python client for connecting to the gRPC gateway.

    It manages the asyncio event loop internally, so all interfaces are synchronous from the outside.
    """

    async def _get_results(
        self,
        inputs: InputType,
        on_done: Callable,
        on_error: Callable = None,
        on_always: Callable = None,
        **kwargs,
    ):
        try:
            self.inputs = inputs
            req_iter = self._get_requests(**kwargs)
            async with grpc.aio.insecure_channel(
                f'{self.args.host}:{self.args.port}',
                options=[
                    ('grpc.max_send_message_length', -1),
                    ('grpc.max_receive_message_length', -1),
                ],
            ) as channel:
                stub = jina_pb2_grpc.JinaRPCStub(channel)
                self.logger.debug(f'connected to {self.args.host}:{self.args.port}')

                cm1 = ProgressBar() if self.show_progress else nullcontext()

                with cm1 as p_bar:
                    async for resp in stub.Call(req_iter):
                        resp.as_typed_request(resp.request_type)
                        resp = resp.as_response()
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

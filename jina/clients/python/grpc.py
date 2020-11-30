__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os

import grpc

from ... import __stop_msg__
from ...excepts import GRPCServerError, BadClientRequestGenerator, BadClient
from ...logging import JinaLogger
from ...proto import jina_pb2_grpc
from ...helper import use_uvloop
from ...peapods.pea import BasePea

if False:
    # fix type-hint complain for sphinx and flake
    import argparse


class AsyncGrpcClient:
    """
    A Base gRPC client which the other python client application can build from.

    """

    def __init__(self, args: 'argparse.Namespace'):
        self.args = args
        if not args.proxy and os.name != 'nt':
            os.unsetenv('http_proxy')
            os.unsetenv('https_proxy')
        self.logger = JinaLogger(self.__class__.__name__, **vars(args))
        self.configure_event_loop()
        self.logger.debug('setting up grpc insecure channel...')
        # A gRPC channel provides a connection to a remote gRPC server.
        self._channel = grpc.aio.insecure_channel(
            f'{args.host}:{args.port_expose}',
            options={
                'grpc.max_send_message_length': -1,
                'grpc.max_receive_message_length': -1,
            }.items(),
        )
        self._stub = jina_pb2_grpc.JinaRPCStub(self._channel)

        # attache response handler
        self.logger.success(f'connected to the gateway at {self.args.host}:{self.args.port_expose}!')
        self.is_closed = False

    def configure_event_loop(self):
        use_uvloop()
        import asyncio
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()

    async def call(self, *args, **kwargs):
        """Calling the gRPC server """
        raise NotImplementedError

    async def __aenter__(self):
        return await self.start()

    async def __exit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self, *args, **kwargs) -> 'AsyncGrpcClient':
        """Wrapping :meth:`call` and provide exception captures
        """
        try:
            await self.call(*args, **kwargs)
        except KeyboardInterrupt:
            self.logger.warning('user cancel the process')
        except grpc.RpcError as rpc_ex:
            # Since this object is guaranteed to be a grpc.Call, might as well include that in its name.
            my_code = rpc_ex.code()
            my_details = rpc_ex.details()
            msg = f'gRPC error: {my_code} {my_details}'
            if my_code == grpc.StatusCode.UNAVAILABLE:
                self.logger.error(
                    f'{msg}\nthe ongoing request is terminated as the server is not available or closed already')
                raise rpc_ex
            elif my_code == grpc.StatusCode.INTERNAL:
                self.logger.error(f'{msg}\ninternal error on the server side')
                raise rpc_ex
            elif my_code == grpc.StatusCode.UNKNOWN and my_details == 'Exception iterating requests!':
                raise BadClientRequestGenerator(f'{msg}\n'
                                                'often the case is that you define/send a bad input iterator to jina, '
                                                'please double check your input iterator') from rpc_ex
            else:
                raise BadClient(msg) from rpc_ex
        finally:
            await self.close()

        return self

    async def close(self) -> None:
        """Gracefully shutdown the client and release all gRPC-related resources """
        if not self.is_closed:
            await self._channel.close()
            self.logger.success(__stop_msg__)
            self.logger.close()
            self.is_closed = True

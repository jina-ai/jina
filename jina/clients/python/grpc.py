import os
from typing import Callable

import grpc

from ...excepts import BadClient
from ...logging.base import get_logger
from ...proto import jina_pb2_grpc

if False:
    # fix type-hint complain for sphinx and flake
    import argparse


class GrpcClient:
    """
    A Base gRPC client which the other python client application can build from.

    """

    def __init__(self, args: 'argparse.Namespace'):
        self.args = args
        if not args.proxy and os.name != 'nt':
            os.unsetenv('http_proxy')
            os.unsetenv('https_proxy')
        self.logger = get_logger(self.__class__.__name__, **vars(args))
        self.logger.debug('setting up grpc insecure channel...')
        # A gRPC channel provides a connection to a remote gRPC server.
        self._channel = grpc.insecure_channel(
            '%s:%d' % (self.args.grpc_host, self.args.grpc_port),
            options={
                'grpc.max_send_message_length': -1,
                'grpc.max_receive_message_length': -1,
            }.items(),
        )
        self.logger.debug('waiting channel to be ready...')
        grpc.channel_ready_future(self._channel).result()

        # create new stub
        self.logger.debug('create new stub...')
        self._stub = jina_pb2_grpc.JinaRPCStub(self._channel)

        # attache response handler
        self.logger.critical('client is ready at %s:%d!' % (self.args.grpc_host, self.args.grpc_port))

    def _call(self, *args, **kwargs):
        """Calling the grpc server """
        raise NotImplementedError

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def start(self, call_fn: Callable = None, *args, **kwargs):
        """Wrapping :func:`call` and provide exception captures

        :param call_fn: function to wrap, when not given then :meth:`self._call` is wrapped
        """

        r = None
        try:
            if call_fn:
                r = call_fn(*args, **kwargs)
            else:
                r = self._call(*args, **kwargs)
        except KeyboardInterrupt:
            self.logger.warning('user cancel the process')
        except grpc.RpcError as rpc_error_call:  # Since this object is guaranteed to be a grpc.Call, might as well include that in its name.
            my_code = rpc_error_call.code()
            my_details = rpc_error_call.details()
            raise BadClient('%s error in grpc: %s '
                            'often the case is that you define/send a bad input iterator to jina, '
                            'please double check your input iterator' % (my_code, my_details))
        finally:
            self.close()

        return r

    def close(self):
        """Gracefully shutdown the client and release all grpc-related resources """
        if self._stub:
            self._channel.close()
            self._stub = None

import os

import grpc

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
        if not args.proxy:
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

    def call(self, *args, **kwargs):
        """Calling the grpc server """
        raise NotImplementedError

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def start(self, *args, **kwargs):
        """Wrapping :func:`call` and provide exception captures """
        try:
            self.call(*args, **kwargs)
        except KeyboardInterrupt:
            self.logger.warning('user cancel the process')
        except Exception as ex:
            self.logger.error(ex)
        finally:
            self.close()

    def close(self):
        """Gracefully shutdown the client and release all grpc-related resources """
        self._channel.close()
        self._stub = None

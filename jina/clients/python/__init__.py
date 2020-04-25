__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from .grpc import GrpcClient
from .helper import ProgressBar
from typing import Iterator, Callable, Union

from .grpc import GrpcClient
from .helper import ProgressBar
from ...excepts import BadClient
from ...logging.profile import TimeContext
from ...proto import jina_pb2
from typing import Iterator, Callable, Union

from .grpc import GrpcClient
from .grpc import GrpcClient
from .helper import ProgressBar
from .helper import ProgressBar
from ...excepts import BadClient
from ...logging.profile import TimeContext
from ...proto import jina_pb2

if False:
    # fix type-hint complain for sphinx and flake
    import argparse


class PyClient(GrpcClient):
    """A simple Python client for connecting to the gateway """

    def __init__(self, args: 'argparse.Namespace'):
        """

        :param args: args provided by the CLI
        :param delay: if ``True`` then the client starts sending request after initializing, otherwise one needs to set
            the :attr:`raw_bytes` before using :func:`start` or :func:`call`
        """
        super().__init__(args)
        self._raw_bytes = None

    def call(self, callback: Callable[['jina_pb2.Message'], None] = None) -> None:
        """ Calling the server, better use :func:`start` instead.

        :param callback: a callback function, invoke after every response is received
        """
        kwargs = vars(self.args)
        kwargs['data'] = self.raw_bytes

        from . import request
        tname = self.args.mode
        req_iter = getattr(request, tname)(**kwargs)

        with ProgressBar(task_name=tname) as p_bar, TimeContext(tname):
            for resp in self._stub.Call(req_iter):
                if callback:
                    try:
                        if self.args.callback_on_body:
                            resp = getattr(resp, resp.WhichOneof('body'))
                        callback(resp)
                    except Exception as ex:
                        raise BadClient('error in client\'s callback: %s' % ex)
                p_bar.update(self.args.batch_size)

    @property
    def raw_bytes(self) -> Union[Iterator['jina_pb2.Document'], Iterator[bytes], Callable]:
        """ An iterator of bytes, each element represents a document's raw content,
        i.e. ``raw_bytes`` defined int the protobuf
        """
        if self._raw_bytes:
            return self._raw_bytes
        else:
            raise BadClient('raw_bytes is empty or not set')

    @raw_bytes.setter
    def raw_bytes(self, bytes_gen: Union[Iterator['jina_pb2.Document'], Iterator[bytes], Callable]):
        if self._raw_bytes:
            self.logger.warning('raw_bytes is not empty, overrided')
        if hasattr(bytes_gen, '__call__'):
            self._raw_bytes = bytes_gen()
        else:
            self._raw_bytes = bytes_gen

    def dry_run(self) -> bool:
        """Send a DRYRUN request to the server, passing through all pods on the server
        useful for testing connectivity and debugging

        :return: if dry run is successful or not
        """

        def req_gen():
            req = jina_pb2.Request()
            req.control.command = jina_pb2.Request.ControlRequest.DRYRUN
            yield req

        for resp in self._stub.Call(req_gen()):
            self.logger.info(resp)
            return True

        return False

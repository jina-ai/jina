from typing import Iterator, Callable, Union

from .grpc import GrpcClient
from .helper import ProgressBar
from ...excepts import BadClient
from ...helper import kwargs2list
from ...logging import get_logger
from ...logging.profile import TimeContext
from ...proto import jina_pb2

if False:
    # fix type-hint complain for sphinx and flake
    import argparse


class SpawnPeaPyClient(GrpcClient):

    def __init__(self, args: 'argparse.Namespace', pea_args: 'argparse.Namespace'):
        super().__init__(args)
        self.pea_args = pea_args

    def _call(self):
        _args = kwargs2list(vars(self.pea_args))
        req = jina_pb2.SpawnRequest()
        req.pea.args.extend(_args)
        logger = get_logger('🌐', **vars(self.args), fmt_str='🌐 %(message)s')
        for resp in self._stub.Spawn(req):
            for l in resp.logs:
                logger.info(l)


class SpawnPodPyClient(GrpcClient):

    def __init__(self, args: 'argparse.Namespace', pod_args: 'argparse.Namespace'):
        super().__init__(args)
        self.pod_args = pod_args

    def _call(self):
        _args = kwargs2list(vars(self.pod_args))
        req = jina_pb2.SpawnRequest()
        req.pod.args.extend(_args)
        logger = get_logger('🌐', **vars(self.args), fmt_str='🌐 %(message)s')
        for resp in self._stub.Spawn(req):
            for l in resp.logs:
                logger.info(l)


class PyClient(GrpcClient):
    """A simple Python client for connecting to the frontend """

    def __init__(self, args: 'argparse.Namespace'):
        """

        :param args: args provided by the CLI
        :param delay: if ``True`` then the client starts sending request after initializing, otherwise one needs to set
            the :attr:`raw_bytes` before using :func:`start` or :func:`call`
        """
        super().__init__(args)
        self._raw_bytes = None

    def _call(self, callback: Callable[['jina_pb2.Message'], None] = None) -> None:
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
                        callback(resp)
                    except Exception as ex:
                        raise BadClient('error in client\'s callback: %s' % ex)
                p_bar.update()

    @property
    def raw_bytes(self) -> Union[Iterator['jina_pb2.Document'], Iterator[bytes]]:
        """ An iterator of bytes, each element represents a document's raw content,
        i.e. ``raw_bytes`` defined int the protobuf
        """
        if self._raw_bytes:
            return self._raw_bytes
        else:
            raise BadClient('raw_bytes is empty or not set')

    @raw_bytes.setter
    def raw_bytes(self, bytes_gen: Union[Iterator['jina_pb2.Document'], Iterator[bytes]]):
        if self._raw_bytes:
            self.logger.warning('raw_bytes is not empty, overrided')
        self._raw_bytes = bytes_gen

    def dry_run(self) -> bool:
        """Send a DRYRUN request to the server, passing through all pods on the server
        useful for testing connectivity and debuging

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

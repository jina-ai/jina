from typing import Iterator, Callable, Union, Dict

from .grpc import GrpcClient
from .helper import ProgressBar
from ... import __default_host__
from ...excepts import BadClient
from ...helper import kwargs2list
from ...logging import get_logger
from ...logging.profile import TimeContext
from ...main.parser import set_pea_parser
from ...proto import jina_pb2

if False:
    # fix type-hint complain for sphinx and flake
    import argparse


class SpawnPeaPyClient(GrpcClient):
    body_tag = 'pea'

    def __init__(self, args: 'argparse.Namespace'):
        super().__init__(args)
        self.args = args
        # set the host back to local, as for the remote, it is running "locally"
        self.args.host = __default_host__
        self.callback_on_first = True

    def call(self, set_ready: Callable = None):
        """

        :param set_ready: :func:`set_ready` signal from :meth:`jina.peapods.peas.Pea.set_ready`
        :return:
        """
        req = jina_pb2.SpawnRequest()
        getattr(req, self.body_tag).args.extend(kwargs2list(vars(self.args)))
        self.remote_logging(req, set_ready)

    def remote_logging(self, req, set_ready):
        logger = get_logger('🌐', **vars(self.args), fmt_str='🌐 %(message)s')
        for resp in self._stub.Spawn(req):
            if set_ready and self.callback_on_first:
                set_ready()
                self.callback_on_first = False
            logger.info(resp.log_record)


class SpawnPodPyClient(SpawnPeaPyClient):
    body_tag = 'pod'


class SpawnDictPodPyClient(SpawnPeaPyClient):

    def __init__(self, peas_args: Dict):
        inited = False
        for k in peas_args.values():
            if k:
                if not inited:
                    # any pea will do, we just need its host and port_grpc
                    super().__init__(k)
                    inited = True
                k.host = __default_host__
        self.peas_args = peas_args
        self.callback_on_first = True

    @staticmethod
    def convert2pea_args(args: 'argparse.Namespace'):
        return kwargs2list(vars(set_pea_parser().parse_known_args(kwargs2list(vars(args)))[0]))

    def call(self, set_ready: Callable = None):
        req = jina_pb2.SpawnRequest()
        if self.peas_args['head']:
            req.cust_pod.head.args.extend(self.convert2pea_args(self.peas_args['head']))
        if self.peas_args['tail']:
            req.cust_pod.tail.args.extend(self.convert2pea_args(self.peas_args['tail']))
        if self.peas_args['peas']:
            for q in self.peas_args['peas']:
                _a = req.cust_pod.peas.add()
                _a.args.extend(self.convert2pea_args(q))

        self.remote_logging(req, set_ready)


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

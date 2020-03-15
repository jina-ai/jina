from typing import Callable, Dict

from .pea import BasePea
from .pod import BasePod
from .zmq import Zmqlet, send_ctrl_message
from .. import __default_host__
from ..clients.python import GrpcClient
from ..helper import kwargs2list
from ..logging import get_logger
from ..main.parser import set_pea_parser
from ..proto import jina_pb2

if False:
    import argparse


class SpawnPeaHelper(GrpcClient):
    body_tag = 'pea'

    def __init__(self, args: 'argparse.Namespace'):
        super().__init__(args)
        self.ctrl_addr, self.ctrl_with_ipc = Zmqlet.get_ctrl_address(args)
        self.args = args
        # set cli to none if exist
        if hasattr(self.args, 'cli'):
            self.args.cli = None
        # set the host back to local, as for the remote, it is running "locally"
        self.args.host = __default_host__
        self.callback_on_first = True

    def call(self, set_ready: Callable = None):
        """

        :param set_ready: :func:`set_ready` signal from :meth:`jina.peapods.peas.BasePea.set_ready`
        :return:
        """
        req = jina_pb2.SpawnRequest()
        getattr(req, self.body_tag).args.extend(kwargs2list(vars(self.args)))
        self.remote_logging(req, set_ready)

    def remote_logging(self, req, set_ready):
        logger = get_logger('🌏', **vars(self.args), fmt_str='🌏 %(message)s')
        for resp in self._stub.Spawn(req):
            if set_ready and self.callback_on_first:
                set_ready()
                self.callback_on_first = False
            logger.info(resp.log_record)

    def close(self):
        if not self.is_closed:
            send_ctrl_message(self.ctrl_addr, jina_pb2.Request.ControlRequest.TERMINATE,
                              timeout=self.args.timeout_ctrl)
            super().close()


class SpawnPodHelper(SpawnPeaHelper):
    body_tag = 'pod'


class SpawnDictPodHelper(SpawnPeaHelper):

    def __init__(self, peas_args: Dict):
        inited = False
        for k in peas_args.values():
            if k:
                if not isinstance(k, list):
                    k = [k]
                if not inited:
                    # any pea will do, we just need its host and port_grpc
                    super().__init__(k[0])
                    inited = True
                for kk in k:
                    kk.host = __default_host__
                    if hasattr(kk, 'cli'):
                        kk.cli = None
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


class RemotePea(BasePea):
    """A BasePea that spawns another pea remotely """

    def __init__(self, args: 'argparse.Namespace'):
        if hasattr(args, 'host') and args.host != __default_host__:
            super().__init__(args)
        else:
            raise ValueError(
                '%r requires "args.host" to be set, and it should not be %s' % (self.__class__, __default_host__))

    def post_init(self):
        pass

    def event_loop_start(self):
        self.remote_pea = SpawnPeaHelper(self.args)
        self.remote_pea.start(self.set_ready)  # auto-close after


class RemotePod(BasePod):
    """A BasePea that spawns another pea remotely """

    def __init__(self, args: 'argparse.Namespace'):
        if hasattr(args, 'host') and args.host != __default_host__:
            super().__init__(args)
        else:
            raise ValueError(
                '%r requires "args.host" to be set, and it should not be %s' % (self.__class__, __default_host__))
        self._pod_args = args

    def start(self):
        self.stack.enter_context(SpawnPodHelper(self._pod_args))

    def close(self):
        if hasattr(self, 'remote_pod'):
            self.remote_pod.close()

__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import time

from . import BaseDriver
from ..excepts import UnknownControlCommand, RequestLoopEnd, NoExplicitMessage
from ..proto import jina_pb2, is_data_request


class ControlReqDriver(BaseDriver):
    """Handling the control request, by default it is installed for all :class:`jina.peapods.pea.BasePea`"""

    def __call__(self, *args, **kwargs):
        if self.req.command == jina_pb2.Request.ControlRequest.TERMINATE:
            self.envelope.status.code = jina_pb2.Status.SUCCESS
            raise RequestLoopEnd
        elif self.req.command == jina_pb2.Request.ControlRequest.STATUS:
            self.envelope.status.code = jina_pb2.Status.READY
            for k, v in vars(self.pea.args).items():
                self.req.args[k] = str(v)
        else:
            raise UnknownControlCommand('don\'t know how to handle %s' % self.req)


class LogInfoDriver(BaseDriver):
    """Log output the request info"""

    def __init__(self, field: str = 'msg', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field = field

    def __call__(self, *args, **kwargs):
        self.logger.info(getattr(self, self.field, 'msg'))


class WaitDriver(BaseDriver):
    """Wait for some seconds"""

    def __call__(self, *args, **kwargs):
        time.sleep(5)


class ForwardDriver(BaseDriver):
    """Forward the message to next pod"""

    def __call__(self, *args, **kwargs):
        pass


class RouteDriver(ControlReqDriver):
    """A simple load balancer forward message to the next available pea

    - The dealer never receives a control request from the router,
      everytime it finishes a job and send via out_sock, it returns the envelope with control
      request idle back to the router. The dealer also sends control request idle to the router
      when it first starts.

    - The router receives request from both dealer and upstream pusher.
      if it is a upstream request, use LB to schedule the receiver, mark it in the envelope
      if it is a control request in

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.idle_dealer_ids = set()
        self.is_pollin_paused = False

    def __call__(self, *args, **kwargs):
        if is_data_request(self.req):
            self.logger.debug(self.idle_dealer_ids)
            if self.idle_dealer_ids:
                dealer_id = self.idle_dealer_ids.pop()
                self.envelope.receiver_id = dealer_id
                if not self.idle_dealer_ids:
                    self.pea.zmqlet.pause_pollin()
                    self.is_pollin_paused = True
            else:
                raise RuntimeError('if this router connects more than one dealer, '
                                   'then this error should never be raised. often when it '
                                   'is raised, some Pods must fail to start, so please go '
                                   'up and check the first error message in the log')
        elif self.req.command == jina_pb2.Request.ControlRequest.IDLE:
            self.idle_dealer_ids.add(self.envelope.receiver_id)
            self.logger.debug(f'{self.envelope.receiver_id} is idle')
            if self.is_pollin_paused:
                self.pea.zmqlet.resume_pollin()
                self.is_pollin_paused = False
            raise NoExplicitMessage
        else:
            super().__call__(*args, **kwargs)

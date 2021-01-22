__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import time

from google.protobuf.json_format import MessageToJson

from . import BaseDriver
from .querylang.queryset.dunderkey import dunder_get
from ..excepts import UnknownControlCommand, RuntimeTerminated, NoExplicitMessage
from ..proto import jina_pb2


class BaseControlDriver(BaseDriver):
    """Control driver does not have access to the executor and it
    often works directly with protobuf layer instead Jina primitive types"""

    @property
    def envelope(self) -> 'jina_pb2.EnvelopeProto':
        """Get the current request, shortcut to ``self.runtime.message``"""
        return self.msg.envelope


class LogInfoDriver(BaseControlDriver):
    """Log output the request info"""

    def __init__(self, key: str = 'request', json: bool = True, *args, **kwargs):
        """
        :param key: (str) that represents a first level or nested key in the dict
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.key = key
        self.json = json

    def __call__(self, *args, **kwargs):
        data = dunder_get(self.msg.as_pb_object, self.key)
        if self.json:
            self.logger.info(
                MessageToJson(data)
            )
        else:
            self.logger.info(data)


class WaitDriver(BaseControlDriver):
    """Wait for some seconds, mainly for demo purpose"""

    def __call__(self, *args, **kwargs):
        time.sleep(5)


class ControlReqDriver(BaseControlDriver):
    """Handling the control request, by default it is installed for all :class:`jina.peapods.runtime.BasePea`"""

    def __call__(self, *args, **kwargs):
        if self.req.command == 'TERMINATE':
            self.envelope.status.code = jina_pb2.StatusProto.SUCCESS
            raise RuntimeTerminated
        elif self.req.command == 'STATUS':
            self.envelope.status.code = jina_pb2.StatusProto.READY
            self.req.args = vars(self.runtime.args)
        else:
            raise UnknownControlCommand(f'don\'t know how to handle {self.req.command}')


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

    def __init__(self, raise_no_dealer: bool = False, *args, **kwargs):
        """
        :param raise_no_dealer: raise a RuntimeError when no available dealer
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.idle_dealer_ids = set()
        self.is_pollin_paused = False
        self.raise_no_dealer = raise_no_dealer

    def __call__(self, *args, **kwargs):
        if self.msg.is_data_request:
            self.logger.debug(self.idle_dealer_ids)
            if self.idle_dealer_ids:
                dealer_id = self.idle_dealer_ids.pop()
                self.envelope.receiver_id = dealer_id
                if not self.idle_dealer_ids:
                    self.runtime._zmqlet.pause_pollin()
                    self.is_pollin_paused = True
            elif self.raise_no_dealer:
                raise RuntimeError('if this router connects more than one dealer, '
                                   'then this error should never be raised. often when it '
                                   'is raised, some Pods must fail to start, so please go '
                                   'up and check the first error message in the log')
            # else:
            #    this FALLBACK to trivial message pass
            #
            # Explanation on the logic here:
            # there are two cases that when `idle_dealer_ids` is empty
            # (1) this driver is used in a PUSH-PULL fan-out setting,
            # where no dealer is registered in the first place, so `idle_dealer_ids` is empty
            # all the time
            # (2) this driver is used in a ROUTER-DEALER fan-out setting,
            # where some dealer is broken/fails to start, so `idle_dealer_ids` is empty
        elif self.req.command == 'IDLE':
            self.idle_dealer_ids.add(self.envelope.receiver_id)
            self.logger.debug(f'{self.envelope.receiver_id} is idle, now I know these idle peas {self.idle_dealer_ids}')
            if self.is_pollin_paused:
                self.runtime._zmqlet.resume_pollin()
                self.is_pollin_paused = False
            raise NoExplicitMessage
        else:
            super().__call__(*args, **kwargs)


class ForwardDriver(RouteDriver):
    """Alias to :class:`RouteDriver`"""


class ReduceDriver(RouteDriver):
    """Alias to :class:`RouteDriver`"""

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


def split_message_by_mode_id(input_msg: 'jina_pb2.Message', num_nodes: int):
    req_type = input_msg.request.WhichOneof('body')
    output_msgs = []
    for mode_id in range(num_nodes):
        msg = jina_pb2.Message()
        # could it be too expensive?
        msg.CopyFrom(input_msg)
        getattr(msg.request, req_type).ClearField('docs')
        output_msgs.append(msg)
    docs = getattr(input_msg.request, req_type).docs
    for doc in docs:
        mode_id = doc.mode_id
        getattr(output_msgs[mode_id].request, req_type).docs.append(doc)
    return output_msgs


class SplitRouteDriver(ControlReqDriver):
    """This driver forward in a load balanced way, messages to different peas, depending on the
    requested mode_id.

    For simplicity, let's assume that only one dealer at the same can be requesting messages from a `mode_id`.

    It splits the incoming message into different output messages to group documents by `mode_id`
    """

    def __init__(self, num_modes: int = 1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_modes = num_modes
        self.idle_dealer_ids = [None] * num_modes
        self.is_pollin_paused = False
        self.mode_idx_map = {}

    def __call__(self, *args, **kwargs):
        if is_data_request(self.req):
            # clear messages from old processing
            self.output_msgs.clear()
            self.output_msgs = split_message_by_mode_id(self.processing_msg, self.num_modes)
            for mode_id, message in enumerate(self.output_msgs):
                # TODO: Consider case where message is missing one or two modes, need a mapping from idx, to mode_id.
                # TODO: How do we handle synchronization, 2 dealers of different mode_id may consume messages at different rate.
                if self.idle_dealer_ids[mode_id]:
                    self.output_msgs[mode_id].envelope.receiver_id = self.idle_dealer_ids[mode_id]
                    self.idle_dealer_ids[mode_id] = None

            for mode_id in range(self.num_modes):
                if self.idle_dealer_ids[mode_id] is not None:
                    break
            self.pea.zmqlet.pause_pollin()
            self.is_pollin_paused = True
        elif self.req.command == jina_pb2.Request.ControlRequest.IDLE:
            mode_id_req = self.req.mode_id
            if self.idle_dealer_ids[mode_id_req] is not None:
                raise RuntimeError(f'Should never happen, more than one dealer are expecting'
                                   f' to receive messages for mode_id {mode_id_req}:'
                                   f' {self.idle_dealer_ids[mode_id_req]} and {self.envelope.receiver_id}.from.'
                                   f'You may have defined a Flow where more than one outcoming'
                                   f' pod is requesting the same mode_id from the same incoming pod')

            self.idle_dealer_ids[mode_id_req] = self.envelope.receiver_id
            self.logger.debug(f'{self.envelope.receiver_id} is idle and requests documents of mode {mode_id_req}')
            if self.is_pollin_paused:
                self.pea.zmqlet.resume_pollin()
                self.is_pollin_paused = False

            # not nice to raise an Exception for what is an expected behavior
            raise NoExplicitMessage
        else:
            super().__call__(*args, **kwargs)

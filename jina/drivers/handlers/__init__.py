"""`Handler` is a function of processing a protobuf message.
Unlike `hook` functions, handler often works directly on request, not the message """

import time
from typing import List, Callable

from ...excepts import UnknownControlCommand, EventLoopEnd
from ...proto import jina_pb2

if False:
    # fix type-hint complain for sphinx and flake
    from ...peapods.pea import Pea


def handler_fn_template(exec_fn: Callable, pea: 'Pea',
                        req: 'jina_pb2.Request',
                        msg: 'jina_pb2.Message',
                        pre_reqs: List['jina_pb2.Request'],
                        prev_msgs: List['jina_pb2.Message'], *args, **kwargs) -> None:
    """ A template of the handler function, it will modify ``req`` inplace.

    :param exec_fn: the function of :class:`jina.executors.BaseExecutor` to call
    :param pea: :class:`jina.peapods.pea.Pea` context
    :param req: the request body inside the protobuf message
    :param msg: the protobuf message to be processed
    :param pre_reqs: previous requests collected, useful in reduce handler
    :param prev_msgs: previous messages collected, useful in reduce handler

    .. note::
        A handler function's name starts with ``handler_`` as the convention

    To access the executor in Pea, use ``pea.executor``.
    """
    raise NotImplementedError('this function serves as a template for documentation')


def handler_control_req(exec_fn, pea, req, msg, *args, **kwargs):
    """Handling the control request, by default it is installed for all :class:`jina.peapods.pea.Pea`"""
    if req.command == jina_pb2.Request.ControlRequest.TERMINATE:
        msg.envelope.status = jina_pb2.Envelope.SUCCESS
        raise EventLoopEnd
    elif req.command == jina_pb2.Request.ControlRequest.STATUS:
        msg.envelope.status = jina_pb2.Envelope.READY
    else:
        raise UnknownControlCommand('dont know how to handle %s' % req)


def handler_log_req(exec_fn, pea, req, msg, *args, **kwargs):
    """Log output the request info"""
    pea.logger.info(req)


def handler_wait_req(*args, **kwargs):
    """Wait for some seconds"""
    time.sleep(5)


def handler_route(*args, **kwargs):
    """Route the message to next pod"""
    pass

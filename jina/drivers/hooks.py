"""`Hook` is a function of processing a protobuf message before/after the `handler` function"""

from .helper import routes2str, add_route
from ..proto import jina_pb2


def hook_fn_template(pea: 'Pea', msg: 'jina_pb2.Message', *args, **kwargs) -> None:
    """ A template of the hook function, it will modify ``msg`` inplace.

    :param pea: :class:`jina.peapods.pea.Pea` context
    :param msg: the protobuf message to be processed

    .. note::
        A hook function's name starts with ``hook_`` as the convention
    """
    raise NotImplementedError('this function serves as a template for documentation')


def hook_add_route_to_msg(pea, msg: 'jina_pb2.Message', *args, **kwargs):
    """Add the current ``Pea`` info to the route of the message """
    pea._msg_old_type = msg.request.WhichOneof('body')
    pea.logger.info('received "%s" from %s' % (pea._msg_old_type, routes2str(msg, flag_current=True)))
    add_route(msg.envelope, pea.name, pea.args.identity)


def hook_update_timestamp(pea, msg: 'jina_pb2.Message', *args, **kwargs):
    """Update the timestamp in the route of the message"""
    msg.envelope.routes[-1].end_time.GetCurrentTime()

import time

from . import BaseDriver
from ..excepts import UnknownControlCommand, EventLoopEnd
from ..proto import jina_pb2


class ControlReqDriver(BaseDriver):
    """Handling the control request, by default it is installed for all :class:`jina.peapods.pea.BasePea`"""

    def __call__(self, *args, **kwargs):
        if self.req.command == jina_pb2.Request.ControlRequest.TERMINATE:
            self.msg.envelope.status = jina_pb2.Envelope.SUCCESS
            raise EventLoopEnd
        elif self.req.command == jina_pb2.Request.ControlRequest.STATUS:
            self.msg.envelope.status = jina_pb2.Envelope.READY
            for k, v in vars(self.pea.args).items():
                self.req.args[k] = str(v)
        elif self.req.command == jina_pb2.Request.ControlRequest.DRYRUN:
            self.msg.envelope.status = jina_pb2.Envelope.READY
        else:
            raise UnknownControlCommand('don\'t know how to handle %s' % self.req)


class LogInfoDriver(BaseDriver):
    """Log output the request info"""

    def __call__(self, *args, **kwargs):
        self.logger.info(self.req)


class WaitDriver(BaseDriver):
    """Wait for some seconds"""

    def __call__(self, *args, **kwargs):
        time.sleep(5)


class ForwardDriver(BaseDriver):
    """Route the message to next pod"""

    def __call__(self, *args, **kwargs):
        pass

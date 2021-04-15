__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import re
import time

from google.protobuf.json_format import MessageToJson

from . import BaseDriver
from ..excepts import UnknownControlCommand, RuntimeTerminated, NoExplicitMessage
from ..proto import jina_pb2
from ..types.querylang.queryset.dunderkey import dunder_get


class BaseControlDriver(BaseDriver):
    """Control driver does not have access to the executor and it
    often works directly with protobuf layer instead Jina primitive types"""

    @property
    def envelope(self) -> 'jina_pb2.EnvelopeProto':
        """Get the current request, shortcut to ``self.runtime.message``


        .. # noqa: DAR201
        """
        return self.msg.envelope


class LogInfoDriver(BaseControlDriver):
    """
    Log output the request info

    :param key: (str) that represents a first level or nested key in the dict
    :param json: (bool) indicating if the log output should be formatted as json
    :param args: additional positional arguments which are just used for the parent initialization
    :param kwargs: additional key value arguments which are just used for the parent initialization
    """

    def __init__(self, key: str = 'request', json: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.key = key
        self.json = json

    def __call__(self, *args, **kwargs):
        """Log the information.

        :param args: unused
        :param kwargs: unused
        """
        data = dunder_get(self.msg.proto, self.key)
        if self.json:
            self.logger.info(MessageToJson(data))
        else:
            self.logger.info(data)


class WaitDriver(BaseControlDriver):
    """Wait for some seconds, mainly for demo purpose"""

    def __call__(self, *args, **kwargs):
        """Wait for some seconds, mainly for demo purpose


        .. # noqa: DAR101
        """
        time.sleep(5)


class ControlReqDriver(BaseControlDriver):
    """Handling the control request, by default it is installed for all :class:`jina.peapods.peas.BasePea`"""

    def __call__(self, *args, **kwargs):
        """Handle the request controlling.

        :param args: unused
        :param kwargs: unused
        """
        if self.req.command == 'TERMINATE':
            self.envelope.status.code = jina_pb2.StatusProto.SUCCESS
            raise RuntimeTerminated
        elif self.req.command == 'STATUS':
            self.envelope.status.code = jina_pb2.StatusProto.READY
            self.req.args = vars(self.runtime.args)
        elif self.req.command == 'IDLE':
            pass
        elif self.req.command == 'CANCEL':
            pass
        elif self.req.command == 'DUMP':
            self.logger.warning(
                'DUMP command cannot be processed by ControlReqDriver. Use DumpDriver'
            )
        elif self.req.command == 'RELOAD':
            if self.req.targets and self.runtime.__class__.__name__ == 'ZEDRuntime':
                patterns = self.req.targets
                if isinstance(patterns, str):
                    patterns = [patterns]
                for p in patterns:
                    if re.match(p, self.runtime.name):
                        self.logger.info(
                            f'reloading the Executor `{self.runtime._executor.name}` in `{self.runtime.name}`'
                        )
                        self.runtime._load_executor()
                        break
        else:
            raise UnknownControlCommand(f'don\'t know how to handle {self.req.command}')


class RouteDriver(ControlReqDriver):
    """Ensures that data requests are forwarded to the downstream `:class:`BasePea` ensuring
      that the load is balanced between parallel `:class:`BasePea` if the scheduling `:class:`SchedulerType` is LOAD_BALANCE.

    .. note::
        - The dealer never receives a control request from the router,
        every time it finishes a job and sends via out_sock, it returns the envelope with control
        request idle back to the router. The dealer also sends control request idle to the router
        when it first starts.

        - The router receives requests from both dealer and upstream pusher.
         if it is an upstream request, use LB to schedule the receiver,
         mark it in the envelope if it is a control request in

    :param raise_no_dealer: raise a RuntimeError when no available dealer
    :param args: additional positional arguments which are just used for the parent initialization
    :param kwargs: additional key value arguments which are just used for the parent initialization
    """

    def __init__(self, raise_no_dealer: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.idle_dealer_ids = set()
        self.is_polling_paused = False
        self.raise_no_dealer = raise_no_dealer

    def __call__(self, *args, **kwargs):
        """Perform the routing.

        :param args: additional positional arguments which are just used for calling the parent
        :param kwargs: additional key value arguments which are just used for calling the parent


        .. # noqa: DAR401
        """
        if self.msg.is_data_request:
            self.logger.debug(self.idle_dealer_ids)
            if self.idle_dealer_ids:
                dealer_id = self.idle_dealer_ids.pop()
                self.envelope.receiver_id = dealer_id
                if not self.idle_dealer_ids:
                    self.runtime._zmqlet.pause_pollin()
                    self.is_polling_paused = True
            elif self.raise_no_dealer:
                raise RuntimeError(
                    'if this router connects more than one dealer, '
                    'then this error should never be raised. often when it '
                    'is raised, some Pods must fail to start, so please go '
                    'up and check the first error message in the log'
                )
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
            # IDLE requests add the dealer id to the router. Therefore, it knows which dealer would be available for
            # new data requests.
            # CANCEL requests remove the dealer id from the router. Therefore, it can not send any more data requests
            # to the dealer.
        elif self.req.command == 'IDLE':
            self.idle_dealer_ids.add(self.envelope.receiver_id)
            self.logger.debug(
                f'{self.envelope.receiver_id} is idle, now I know these idle peas {self.idle_dealer_ids}'
            )
            if self.is_polling_paused:
                self.runtime._zmqlet.resume_pollin()
                self.is_polling_paused = False
        elif self.req.command == 'CANCEL':
            if self.envelope.receiver_id in self.idle_dealer_ids:
                self.idle_dealer_ids.remove(self.envelope.receiver_id)
        else:
            super().__call__(*args, **kwargs)


class ForwardDriver(RouteDriver):
    """Alias to :class:`RouteDriver`"""


class WhooshDriver(BaseControlDriver):
    """Play a whoosh! sound"""

    def __call__(self, *args, **kwargs):
        """Play a whoosh sound, used in 2021 April fools day

        .. # noqa: DAR101
        """
        import subprocess
        from pkg_resources import resource_filename

        whoosh_mp3 = resource_filename(
            'jina', '/'.join(('resources', 'soundfx', 'whoosh.mp3'))
        )

        subprocess.Popen(
            f'ffplay  -nodisp -autoexit {whoosh_mp3} >/dev/null 2>&1', shell=True
        )

import argparse
from multiprocessing import Event
from typing import Union, Dict, Optional

from .api import get_jinad_api
from ..zmq.base import ZMQManyRuntime
from ....helper import cached_property, ArgNamespace, colored


class JinadRuntime(ZMQManyRuntime):

    def __init__(self, args: Union['argparse.Namespace', Dict]):
        super().__init__(args)
        self.exit_event = Event()
        self.exit_event.clear()
        self.api = get_jinad_api(kind=self.remote_type,
                                 host=self.host,
                                 port=self.port_expose,
                                 logger=self.logger)

    def setup(self):
        # Uploads Pod/Pea context to remote & Creates remote Pod/Pea using :class:`JinadAPI`
        if self._remote_id:
            self.logger.success(f'created remote {self.api.kind} with id {colored(self._remote_id, "cyan")}')

    def run_forever(self):
        # Streams log messages using websocket from remote server.
        # Waits for an `asyncio.Event` to be set to exit out of streaming loop
        self.api.log(remote_id=self._remote_id, event=self.exit_event)

    def cancel(self):
        # Indicates :meth:`run_forever` to exit by setting the `asyncio.Event`
        self.exit_event.set()

    def teardown(self):
        # Closes the remote Pod/Pea using :class:`JinadAPI`
        self.api.delete(remote_id=self._remote_id)

    @cached_property
    def _remote_id(self) -> Optional[str]:
        if self.api.is_alive:
            args = ArgNamespace.flatten_to_dict(self.args)
            if self.api.upload(args):
                return self.api.create(args)

import argparse
import asyncio
from typing import Optional

from .api import get_jinad_api
from ..asyncio.base import AsyncZMQRuntime
from ...zmq import Zmqlet
from ....excepts import DaemonConnectivityError
from ....helper import cached_property, colored


class JinadRuntime(AsyncZMQRuntime):

    def __init__(self, args: 'argparse.Namespace'):
        super().__init__(args)
        self.ctrl_addr = Zmqlet.get_ctrl_address(None, None, True)[0]
        self.timeout_ctrl = args.timeout_ctrl
        self.host = args.host
        self.port_expose = args.port_expose
        self.remote_type = args.remote_type
        self.api = get_jinad_api(kind=self.remote_type,
                                 host=self.host,
                                 port=self.port_expose,
                                 logger=self.logger)

    def setup(self):
        """
        Uploads Pod/Pea context to remote & Creates remote Pod/Pea using :class:`JinadAPI`
        """
        if self._remote_id:
            self.logger.success(f'created remote {self.api.kind} with id {colored(self._remote_id, "cyan")}')
        else:
            self.logger.error(
                f'fail to connect to the daemon at {self.host}:{self.port_expose}, please check:\n'
                f'- is there a typo in {self.host}?\n'
                f'- on {self.host}, are you running `docker run --network host jinaai/jina:latest-daemon`?\n'
                f'- on {self.host}, have you set the security policy to public for all required ports?\n'
                f'- on local, are you behind VPN or proxy?')
            raise DaemonConnectivityError

    async def async_run_forever(self):
        """
        Streams log messages using websocket from remote server
        """
        self._logging_task = asyncio.create_task(
            self.api.logstream(remote_id=self._remote_id, log_id=self.args.log_id)
        )

    async def async_cancel(self):
        """
        Cancels the logging task
        """
        self._logging_task.cancel()

    def teardown(self):
        """
        Closes the remote Pod/Pea using :class:`JinadAPI`
        """
        self.api.delete(remote_id=self._remote_id)

    @cached_property
    def _remote_id(self) -> Optional[str]:
        if self.api.is_alive:
            _args_dict = vars(self.args)
            if self.api.upload(_args_dict):
                return self.api.create(_args_dict)

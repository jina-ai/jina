import time
import asyncio
import argparse
from typing import List, Optional

from ...zmq import Zmqlet, send_ctrl_message
from ..asyncio.base import AsyncZMQRuntime
from ....helper import cached_property, colored
from ....excepts import DaemonConnectivityError
from .client import PeaDaemonClient, WorkspaceDaemonClient


class JinadRuntime(AsyncZMQRuntime):
    """Runtime procedure for Jinad."""

    def __init__(self, args: 'argparse.Namespace'):
        super().__init__(args)
        # Need the `proper` control address to send `activate` and `deactivate` signals, from the pea in the `main` process.
        self.remote_ctrl_addr = self.ctrl_addr
        self.ctrl_addr = Zmqlet.get_ctrl_address(None, None, True)[0]
        self.timeout_ctrl = args.timeout_ctrl
        self.host = args.host
        self.port_expose = args.port_expose
        # TODO: args.timeout_ready is always set to -1 for JinadRuntime so that wait_for_success doesn't fail in Pea,
        # so it can't be used for Client timeout. Setting `timeout` to `None` would wait forever in `DaemonClient`,
        # which is not ideal. Setting it to 15 secs for testing.
        self.workspace_api = WorkspaceDaemonClient(
            host=self.host,
            port=self.port_expose,
            logger=self.logger,
            timeout=15,
        )
        self.pea_api = PeaDaemonClient(
            host=self.host,
            port=self.port_expose,
            logger=self.logger,
            timeout=15,
        )

    def cancel(self):
        """Send terminate control message."""
        # (Joan) I put it here, to show how hacky it is. it recycles the logic to send terminate signal to
        # a remote Pea Runtime by capturing it locally in `_wait_async`. That's why we need to recycle the control addr
        send_ctrl_message(self.ctrl_addr, 'TERMINATE', timeout=self.args.timeout_ctrl)

    def activate(self):
        """Send activate control message."""
        send_ctrl_message(
            self.remote_ctrl_addr, 'ACTIVATE', timeout=self.args.timeout_ctrl
        )

    def deactivate(self):
        """Send deactivate control message."""
        send_ctrl_message(
            self.remote_ctrl_addr, 'DEACTIVATE', timeout=self.args.timeout_ctrl
        )

    def setup(self):
        """
        Uploads Pod/Pea context to remote & Creates remote Pod/Pea using :class:`JinadAPI`
        """
        if self._remote_id:
            self.logger.success(
                f'created a remote {self.pea_api.kind}: {colored(self._remote_id, "cyan")}'
            )

    async def async_run_forever(self):
        """
        Streams log messages using websocket from remote server
        """
        self._logging_task = asyncio.create_task(
            self._sleep_forever()
            if self.args.quiet_remote_logs
            else self.pea_api.logstream(self.args.workspace_id, self._remote_id)
        )

    async def async_cancel(self):
        """
        Cancels the logging task
        """
        self._logging_task.cancel()

    def teardown(self):
        """
        Terminates the remote Workspace/Pod/Pea using :class:`JinadAPI`
        """
        self.pea_api.delete(id=self._remote_id)
        # TODO: don't fail if workspace deletion fails. all peas would make this call. can be optimized
        self.workspace_api.delete(id=self.args.workspace_id)
        super().teardown()

    def create_workspace(self):
        """Create a workspace on remote (includes file upload & docker build)

        :raises DaemonConnectivityError: if remote daemon is not reachable
        :raises RuntimeError: if workspace creation fails
        """
        if not self.workspace_api.alive:
            self.logger.error(
                f'fail to connect to the daemon at {self.host}:{self.port_expose}, please check:\n'
                f'- is there a typo in {self.host}?\n'
                f'- on {self.host}, are you running `docker run --network host jinaai/jina:latest-daemon`?\n'
                f'- on {self.host}, have you set the security policy to public for all required ports?\n'
                f'- on local, are you behind VPN or proxy?'
            )
            raise DaemonConnectivityError

        sleep = 2
        retries = 100
        for retry in range(retries):
            workspace_status = self.workspace_api.get(id=self.args.workspace_id)
            if not workspace_status:
                raise DaemonConnectivityError
            state = workspace_status.get('state', None)
            if not state:
                self.logger.info(
                    f'creating workspace {colored(self.args.workspace_id, "cyan")} on remote. This might take some time.'
                )
                self.workspace_api.post(
                    dependencies=self.args.upload_files,
                    workspace_id=self.args.workspace_id,
                )
            elif state in [
                'PENDING',
                'CREATING',
                'UPDATING',
            ]:  # TODO: move enum from daemon to core
                if retry % 10 == 0:
                    self.logger.info(
                        f'workspace {self.args.workspace_id} is getting created on remote. waiting..'
                    )
                time.sleep(sleep)
            elif state == 'ACTIVE':
                self.logger.success(
                    f'successfully created a remote workspace: {colored(self.args.workspace_id, "cyan")}'
                )
                break
            else:
                raise RuntimeError(f'remote workspace creation failed')

    @cached_property
    def _remote_id(self) -> Optional[str]:
        self.create_workspace()
        pea_id = self.pea_api.post(self.args)
        if not pea_id:
            raise RuntimeError('remote pea creation failed')
        return pea_id

    async def _sleep_forever(self):
        """Sleep forever, no prince will come."""
        await asyncio.sleep(1e10)

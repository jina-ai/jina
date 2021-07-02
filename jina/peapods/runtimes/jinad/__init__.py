import argparse
import asyncio
import time
from typing import Optional

from .client import PeaDaemonClient, WorkspaceDaemonClient
from ....enums import RemoteWorkspaceState
from ..zmq.asyncio import AsyncZMQRuntime
from ...zmq import send_ctrl_message
from .client import PeaDaemonClient, WorkspaceDaemonClient
from ....excepts import DaemonConnectivityError
from ....helper import cached_property, colored


class JinadRuntime(AsyncZMQRuntime):
    """Runtime procedure for Jinad."""

    def __init__(
        self, args: 'argparse.Namespace', ctrl_addr: str, timeout_ctrl: int, **kwargs
    ):
        super().__init__(args, ctrl_addr, **kwargs)
        # Need the `proper` control address to send `activate` and `deactivate` signals, from the pea in the `main`
        # process.
        self.timeout_ctrl = timeout_ctrl
        self.host = args.host
        self.port_expose = args.port_expose
        # NOTE: args.timeout_ready is always set to -1 for JinadRuntime so that wait_for_success doesn't fail in Pea,
        # so it can't be used for Client timeout.
        self.workspace_api = WorkspaceDaemonClient(
            host=self.host,
            port=self.port_expose,
            logger=self.logger,
        )
        self.pea_api = PeaDaemonClient(
            host=self.host,
            port=self.port_expose,
            logger=self.logger,
        )
        # Uploads Pea context to remote & Creates remote Pea using :class:`PeaDaemonClient`
        if self._remote_id:
            self.logger.success(
                f'created a remote {self.pea_api.kind}: {colored(self._remote_id, "cyan")}'
            )

    async def _wait_for_cancel(self):
        """Do NOT override this method when inheriting from :class:`GatewayPea`"""
        while True:
            if self.is_cancel.is_set():
                await self.async_cancel()
                send_ctrl_message(self.ctrl_addr, 'TERMINATE', self.timeout_ctrl)
                return
            else:
                await asyncio.sleep(0.1)

    async def async_run_forever(self):
        """
        Streams log messages using websocket from remote server
        """
        self.is_ready_event.set()
        self._logging_task = asyncio.create_task(
            self._sleep_forever()
            if self.args.quiet_remote_logs
            else self.pea_api.logstream(self._remote_id)
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
                RemoteWorkspaceState.PENDING,
                RemoteWorkspaceState.CREATING,
                RemoteWorkspaceState.UPDATING,
            ]:
                if retry % 10 == 0:
                    self.logger.info(
                        f'workspace {self.args.workspace_id} is getting created on remote. waiting..'
                    )
                time.sleep(sleep)
            elif state == RemoteWorkspaceState.ACTIVE:
                self.logger.success(
                    f'successfully created a remote workspace: {colored(self.args.workspace_id, "cyan")}'
                )
                break
            else:
                raise RuntimeError(f'remote workspace creation failed')

    @cached_property
    def _remote_id(self) -> Optional[str]:
        """Creates a workspace & a pea on remote

        :return: id of rempte pea
        """
        self.create_workspace()
        pea_id = self.pea_api.post(self.args)
        if not pea_id:
            raise RuntimeError('remote pea creation failed')
        return pea_id

    async def _sleep_forever(self):
        """Sleep forever, no prince will come."""
        await asyncio.sleep(1e10)

import argparse
import asyncio
from typing import Optional

from .client import PeaDaemonClient
from ...zmq import Zmqlet, send_ctrl_message
from ..asyncio.base import AsyncZMQRuntime
from ....excepts import DaemonConnectivityError
from ....helper import cached_property, colored, is_yaml_filepath


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
        self.api = PeaDaemonClient(
            host=self.host,
            port=self.port_expose,
            logger=self.logger,
            timeout=self.args.timeout_ready,
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
        """Send activate control message."""
        send_ctrl_message(
            self.remote_ctrl_addr, 'DEACTIVATE', timeout=self.args.timeout_ctrl
        )

    def setup(self):
        """
        Uploads Pod/Pea context to remote & Creates remote Pod/Pea using :class:`JinadAPI`
        """
        if self._remote_id:
            self.logger.success(
                f'created a remote {self.api.kind}: {colored(self._remote_id, "cyan")}'
            )
        else:
            self.logger.error(
                f'fail to connect to the daemon at {self.host}:{self.port_expose}, please check:\n'
                f'- is there a typo in {self.host}?\n'
                f'- on {self.host}, are you running `docker run --network host jinaai/jina:latest-daemon`?\n'
                f'- on {self.host}, have you set the security policy to public for all required ports?\n'
                f'- on local, are you behind VPN or proxy?'
            )
            raise DaemonConnectivityError

    async def async_run_forever(self):
        """
        Streams log messages using websocket from remote server
        """
        self._logging_task = asyncio.create_task(
            self._sleep_forever()
            if self.args.quiet_remote_logs
            else self.api.logstream(self._workspace_id, self._remote_id)
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
        super().teardown()

    @cached_property
    def _remote_id(self) -> Optional[str]:
        if self.api.is_alive:
            upload_files = []
            if is_yaml_filepath(self.args.uses):
                upload_files.append(self.args.uses)

            if is_yaml_filepath(self.args.uses_internal):
                upload_files.append(self.args.uses_internal)

            if self.args.upload_files:
                upload_files.extend(self.args.upload_files)
            else:
                self.logger.warning(
                    f'will upload {upload_files} to remote, to include more local file '
                    f'dependencies, please use `--upload-files`'
                )

            if upload_files:
                workspace_id = self.api.upload(
                    dependencies=list(set(upload_files)),
                    workspace_id=self.args.workspace_id,
                )
                if workspace_id:
                    self.logger.success(
                        f'uploaded to workspace: {colored(workspace_id, "cyan")}'
                    )
                else:
                    raise RuntimeError('can not upload required files to remote')

            _id = self.api.create(self.args)

            # if there is a new workspace_id, then use it
            self._workspace_id = self.api.get_status(_id)['workspace_id']
            return _id

    async def _sleep_forever(self):
        """Sleep forever, no prince will come."""
        await asyncio.sleep(1e10)

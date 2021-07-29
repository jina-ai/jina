import os
import copy
import asyncio
import argparse

from ...zmq import send_ctrl_message
from ....jaml.helper import complete_path
from ....importer import ImportExtensions
from ....enums import replace_enum_to_str
from ..zmq.asyncio import AsyncNewLoopRuntime
from ....excepts import (
    DaemonConnectivityError,
    DaemonPeaCreationFailed,
    DaemonWorkspaceCreationFailed,
)


class JinadRuntime(AsyncNewLoopRuntime):
    """Runtime procedure for JinaD."""

    def __init__(
        self, args: 'argparse.Namespace', ctrl_addr: str, timeout_ctrl: int, **kwargs
    ):
        super().__init__(args, ctrl_addr, **kwargs)
        # Need the `proper` control address to send `activate` and `deactivate` signals, from the pea in the `main`
        # process.
        self.timeout_ctrl = timeout_ctrl

    async def async_setup(self):
        """Create Workspace, Pea on remote JinaD server"""
        with ImportExtensions(required=True):
            # rich & aiohttp are used in `JinaDClient`
            import rich
            import aiohttp
            from daemon.clients import AsyncJinaDClient
            from daemon.models import DaemonID

            assert rich
            assert aiohttp

        # NOTE: args.timeout_ready is always set to -1 for JinadRuntime so that wait_for_success doesn't fail in Pea,
        # so it can't be used for Client timeout.
        self.client = AsyncJinaDClient(
            host=self.args.host, port=self.args.port_expose, logger=self.logger
        )
        if not await self.client.alive:
            raise DaemonConnectivityError

        # Create a remote workspace with upload_files
        self.workspace_id = await self.client.workspaces.create(
            paths=self.args.upload_files,
            id=self.args.workspace_id,
            complete=True,
        )
        if not self.workspace_id:
            self.logger.critical(f'remote workspace creation failed')
            raise DaemonWorkspaceCreationFailed

        payload = replace_enum_to_str(vars(self._mask_args(self.args)))
        # Create a remote Pea in the above workspace
        success, self.pea_id = await self.client.peas.create(
            workspace_id=self.workspace_id, payload=payload
        )
        if not success:
            self.logger.critical(f'remote pea creation failed')
            raise DaemonPeaCreationFailed

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
        """Streams log messages using websocket from remote server"""
        self.is_ready_event.set()
        self.logstream = asyncio.create_task(
            self._sleep_forever()
            if self.args.quiet_remote_logs
            else self.client.logs(id=self.pea_id)
        )

    async def async_cancel(self):
        """Cancels the logstream task, removes the remote Pea & Workspace"""
        self.logstream.cancel()
        await self.client.peas.delete(id=self.pea_id)
        # NOTE: don't fail if workspace deletion fails here
        await self.client.workspaces.delete(id=self.workspace_id)

    async def _sleep_forever(self):
        """Sleep forever, no prince will come."""
        await asyncio.sleep(1e10)

    def _mask_args(self, args: 'argparse.Namespace'):
        _args = copy.deepcopy(args)

        # reset the runtime to ZEDRuntime or ContainerRuntime
        if _args.runtime_cls == 'JinadRuntime':
            # TODO: add jinahub:// and jinahub+docker:// scheme here
            if _args.uses.startswith('docker://'):
                _args.runtime_cls = 'ContainerRuntime'
            else:
                _args.runtime_cls = 'ZEDRuntime'

        # TODO:/NOTE this prevents jumping from remote to another remote (Han: 2021.1.17)
        # _args.host = __default_host__
        # host resetting disables dynamic routing. Use `disable_remote` instead
        _args.disable_remote = True

        # NOTE: on remote relative filepaths should be converted to filename only
        def basename(field):
            if field and not field.startswith('docker://'):
                try:
                    return os.path.basename(complete_path(field))
                except FileNotFoundError:
                    pass
            return field

        for f in ('uses', 'uses_after', 'uses_before', 'py_modules'):
            attr = getattr(_args, f, None)
            if not attr:
                continue
            setattr(_args, f, [basename(m) for m in attr]) if isinstance(
                attr, list
            ) else setattr(_args, f, basename(attr))

        _args.log_config = ''  # do not use local log_config
        _args.upload_files = []  # reset upload files
        _args.noblock_on_start = False  # wait until start success

        changes = []
        for k, v in vars(_args).items():
            if v != getattr(args, k):
                changes.append(f'{k:>30s}: {str(getattr(args, k)):30s} -> {str(v):30s}')
        if changes:
            changes = [
                'note the following arguments have been masked or altered for remote purpose:'
            ] + changes
            self.logger.debug('\n'.join(changes))

        return _args

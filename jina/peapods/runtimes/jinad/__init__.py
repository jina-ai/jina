import os
import copy
import asyncio
import argparse
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Union

from ....enums import SocketType

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

if TYPE_CHECKING:
    import multiprocessing
    import threading
    from ....logging.logger import JinaLogger


class JinadRuntime(AsyncNewLoopRuntime):
    """Runtime procedure for JinaD."""

    def __init__(
        self,
        args: 'argparse.Namespace',
        **kwargs,
    ):
        self.pea_id = None
        self.logstream = None
        super().__init__(args, **kwargs)
        # Need the `proper` control address to send `activate` and `deactivate` signals, from the pea in the `main`
        # process.
        self.ctrl_addr = self.get_control_address(args.host, args.port_ctrl)
        self.timeout_ctrl = args.timeout_ctrl
        self.host = args.host
        self.port_jinad = args.port_jinad

    async def async_setup(self):
        """Create Workspace, Pea on remote JinaD server"""
        with ImportExtensions(required=True):
            # rich & aiohttp are used in `JinaDClient`
            import rich
            import aiohttp
            from daemon.clients import AsyncJinaDClient

            assert rich
            assert aiohttp

        # NOTE: args.timeout_ready is always set to -1 for JinadRuntime so that wait_for_success doesn't fail in Pea,
        # so it can't be used for Client timeout.
        self.client = AsyncJinaDClient(
            host=self.args.host, port=self.args.port_jinad, logger=self.logger
        )

        if not await self.client.alive:
            raise DaemonConnectivityError

        # Create a remote workspace with upload_files
        workspace_id = await self.client.workspaces.create(
            paths=self.filepaths,
            id=self.args.workspace_id,
            complete=True,
        )
        if not workspace_id:
            self.logger.critical(f'remote workspace creation failed')
            raise DaemonWorkspaceCreationFailed

        payload = replace_enum_to_str(vars(self._mask_args()))
        # Create a remote Pea in the above workspace
        success, response = await self.client.peas.create(
            workspace_id=workspace_id, payload=payload
        )
        if not success:
            self.logger.critical(f'remote pea creation failed')
            raise DaemonPeaCreationFailed(response)
        else:
            self.pea_id = response

    async def _wait_for_cancel(self):
        while not self.is_cancel.is_set():
            await asyncio.sleep(0.1)

        send_ctrl_message(self.ctrl_addr, 'TERMINATE', self.timeout_ctrl)

    async def async_run_forever(self):
        """
        Streams log messages using websocket from remote server
        """
        if self.pea_id is not None:
            self.logstream = asyncio.create_task(
                self._sleep_forever()
                if self.args.quiet_remote_logs
                else self.client.logs(id=self.pea_id)
            )

    async def async_cancel(self):
        """Skip cancel for JinadRuntime"""
        pass

    async def async_teardown(self):
        """Cancels the logstream task, removes the remote Pea"""
        if self.logstream is not None:
            self.logstream.cancel()
        if self.pea_id is not None:
            if await self.client.peas.delete(id=self.pea_id):
                self.logger.success(f'Successfully terminated remote Pea {self.pea_id}')
            # Don't delete workspace here, as other Executors might use them.
            # TODO(Deepankar): probably enable an arg here?

    async def _sleep_forever(self):
        """Sleep forever, no prince will come."""
        await asyncio.sleep(1e10)

    @property
    def filepaths(self) -> List[Path]:
        """Get file/directories to be uploaded to remote workspace

        :return: filepaths to be uploaded to remote
        """
        paths = set()
        if not self.args.upload_files:
            self.logger.warning(f'no files passed to upload to remote')
        else:
            for path in self.args.upload_files:
                try:
                    fullpath = Path(complete_path(path))
                    paths.add(fullpath)
                except FileNotFoundError:
                    self.logger.error(f'invalid path {path} passed')

        return list(paths)

    def _mask_args(self):
        cargs = copy.deepcopy(self.args)

        # reset the runtime to ZEDRuntime/GRPCDataRuntime or ContainerRuntime
        if cargs.runtime_cls == 'JinadRuntime':
            if cargs.uses.startswith(('docker://', 'jinahub+docker://')):
                cargs.runtime_cls = 'ContainerRuntime'
            else:
                if cargs.grpc_data_requests:
                    cargs.runtime_cls = 'GRPCDataRuntime'
                else:
                    cargs.runtime_cls = 'ZEDRuntime'

        # TODO:/NOTE this prevents jumping from remote to another remote (Han: 2021.1.17)
        # _args.host = __default_host__
        # host resetting disables dynamic routing. Use `disable_remote` instead
        cargs.disable_remote = True
        cargs.log_config = ''  # do not use local log_config
        cargs.upload_files = []  # reset upload files
        cargs.noblock_on_start = False  # wait until start success

        changes = []
        for k, v in vars(cargs).items():
            if v != getattr(self.args, k):
                changes.append(
                    f'{k:>30s}: {str(getattr(self.args, k)):30s} -> {str(v):30s}'
                )
        if changes:
            changes = [
                'note the following arguments have been masked or altered for remote purpose:'
            ] + changes
            self.logger.debug('\n'.join(changes))

        return cargs

    # Static methods used by the Pea to communicate with the `Runtime` in the separate process

    @staticmethod
    def cancel(
        cancel_event: Union['multiprocessing.Event', 'threading.Event'], **kwargs
    ):
        """
        Signal the runtime to terminate

        :param cancel_event: the cancel event to set
        :param kwargs: extra keyword arguments
        """
        cancel_event.set()

    @staticmethod
    def activate(
        control_address: str,
        timeout_ctrl: int,
        socket_in_type: 'SocketType',
        logger: 'JinaLogger',
        **kwargs,
    ):
        """
        Check if the runtime has successfully started

        :param control_address: the address where the control message needs to be sent
        :param timeout_ctrl: the timeout to wait for control messages to be processed
        :param socket_in_type: the type of input socket, needed to know if is a dealer
        :param logger: the JinaLogger to log messages
        :param kwargs: extra keyword arguments
        """

        def _retry_control_message(
            ctrl_address: str,
            timeout_ctrl: int,
            command: str,
            num_retry: int,
            logger: 'JinaLogger',
        ):
            from ...zmq import send_ctrl_message

            for retry in range(1, num_retry + 1):
                logger.debug(f'Sending {command} command for the {retry}th time')
                try:
                    send_ctrl_message(
                        ctrl_address,
                        command,
                        timeout=timeout_ctrl,
                        raise_exception=True,
                    )
                    break
                except Exception as ex:
                    logger.warning(f'{ex!r}')
                    if retry == num_retry:
                        raise ex

        if socket_in_type == SocketType.DEALER_CONNECT:
            _retry_control_message(
                ctrl_address=control_address,
                timeout_ctrl=timeout_ctrl,
                command='ACTIVATE',
                num_retry=3,
                logger=logger,
            )

    @staticmethod
    def get_control_address(host: str, port: str, **kwargs):
        """
        Get the control address for a runtime with a given host and port

        :param host: the host where the runtime works
        :param port: the control port where the runtime listens
        :param kwargs: extra keyword arguments
        :return: The corresponding control address
        """
        from ...zmq import Zmqlet

        return Zmqlet.get_ctrl_address(host, port, False)[0]

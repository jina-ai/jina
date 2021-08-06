import os
import copy
import asyncio
import argparse
from typing import Union

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

if False:
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
        super().__init__(args, **kwargs)
        # Need the `proper` control address to send `activate` and `deactivate` signals, from the pea in the `main`
        # process.
        self.ctrl_addr = self.get_control_address(args.host, args.port_ctrl)
        self.timeout_ctrl = args.timeout_ctrl
        self.host = args.host
        self.port_expose = args.port_expose

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
        while not self.is_cancel.is_set():
            await asyncio.sleep(0.1)

        await self.async_cancel()
        send_ctrl_message(self.ctrl_addr, 'TERMINATE', self.timeout_ctrl)

    async def async_run_forever(self):
        """
        Streams log messages using websocket from remote server
        """
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

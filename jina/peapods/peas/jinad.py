import copy
import asyncio
import argparse
import threading
import multiprocessing
from pathlib import Path
from typing import TYPE_CHECKING, List, Union

from . import BasePea
from .helper import _get_worker
from ...helper import get_or_reuse_loop
from ...jaml.helper import complete_path
from ...importer import ImportExtensions
from ...enums import replace_enum_to_str
from ...logging.logger import JinaLogger
from ...excepts import (
    DaemonConnectivityError,
    DaemonPeaCreationFailed,
    DaemonWorkspaceCreationFailed,
)

if TYPE_CHECKING:
    import argparse


class JinaDProcessTarget:
    """Target to be executed on JinaD Process"""

    def __call__(
        self,
        args: 'argparse.Namespace',
        is_started: Union['multiprocessing.Event', 'threading.Event'],
        is_shutdown: Union['multiprocessing.Event', 'threading.Event'],
        is_ready: Union['multiprocessing.Event', 'threading.Event'],
        is_cancelled: Union['multiprocessing.Event', 'threading.Event'],
    ):
        """Method responsible to manage a remote Pea

        This method is the target for the Pea's `thread` or `process`

        .. note::
            Please note that env variables are process-specific. Subprocess inherits envs from
            the main process. But Subprocess's envs do NOT affect the main process. It does NOT
            mess up user local system envs.

        :param args: namespace args from the Pea
        :param is_started: concurrency event to communicate runtime is properly started. Used for better logging
        :param is_shutdown: concurrency event to communicate runtime is terminated
        :param is_ready: concurrency event to communicate runtime is ready to receive messages
        :param is_cancelled: concurrency event to receive cancelling signal from the Pea. Needed by some runtimes
        """
        self.args = args
        self.is_started = is_started
        self.is_shutdown = is_shutdown
        self.is_ready = is_ready
        self.is_cancelled = is_cancelled
        self.pea_id = None
        self.logstream = None
        self.logger = JinaLogger('RemotePea', **vars(args))
        get_or_reuse_loop().run_until_complete(self.run())

    async def run(self):
        """Manage a remote Pea"""
        try:
            await self.create_remote_pea()
        except Exception as ex:
            self.logger.error(
                f'{ex!r} while starting a remote Pea'
                + f'\n add "--quiet-error" to suppress the exception details'
                if not self.args.quiet_error
                else '',
                exc_info=not self.args.quiet_error,
            )
        else:
            self.is_started.set()
            self.is_ready.set()
            self.logstream: asyncio.Task = asyncio.create_task(self.stream_logs())
            await self._wait_until_cancelled()
        finally:
            if not self.logstream.done() or not self.logstream.cancelled():
                self.logstream.cancel()
            await self.terminate_remote_pea()
            self.is_shutdown.set()

    async def create_remote_pea(self):
        """Create Workspace, Pea on remote JinaD server"""
        with ImportExtensions(required=True):
            # rich & aiohttp are used in `AsyncJinaDClient`
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

    async def stream_logs(self):
        """Streams log messages from remote server

        :return: logstreaming task
        """
        if self.pea_id is not None:
            return (
                self._sleep_forever()
                if self.args.quiet_remote_logs
                else self.client.logs(id=self.pea_id)
            )

    async def _sleep_forever(self):
        """Sleep forever, no prince will come."""
        await asyncio.sleep(1e10)

    async def _wait_until_cancelled(self):
        while not self.is_cancelled.is_set():
            await asyncio.sleep(0.1)

    async def terminate_remote_pea(self):
        """Cancels the logstream task, removes the remote Pea"""
        if self.logstream is not None:
            self.logstream.cancel()
        if self.pea_id is not None:
            if await self.client.peas.delete(id=self.pea_id):
                self.logger.success(f'Successfully terminated remote Pea {self.pea_id}')
            # Don't delete workspace here, as other Executors might use them.
            # TODO(Deepankar): probably enable an arg here?

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

        # reset the runtime to WorkerRuntime or ContainerRuntime
        if cargs.runtime_cls == 'JinadRuntime':
            if cargs.uses.startswith(('docker://', 'jinahub+docker://')):
                cargs.runtime_cls = 'ContainerRuntime'
            else:
                cargs.runtime_cls = 'WorkerRuntime'

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


class JinaDPea(BasePea):
    """Manages a remote Pea by handling a separate Process / Thread"""

    def __init__(self, args: 'argparse.Namespace'):
        super().__init__(args)
        self.worker = _get_worker(
            args=args,
            target=JinaDProcessTarget(),
            kwargs={
                'args': args,
                'name': self.name,
                'envs': self._envs,
                'is_started': self.is_started,
                'is_shutdown': self.is_shutdown,
                'is_ready': self.is_ready,
                'is_cancelled': self.cancel_event,
            },
        )

    def start(self):
        """Start the JinaD Process (to manage remote Pea).
        .. #noqa: DAR201
        """
        self.worker.start()
        if not self.args.noblock_on_start:
            self.wait_start_success()
        return self

    def join(self, *args, **kwargs):
        """Joins the Pea.
        This method calls :meth:`join` in :class:`threading.Thread` or :class:`multiprocesssing.Process`.

        :param args: extra positional arguments to pass to join
        :param kwargs: extra keyword arguments to pass to join
        """
        self.logger.debug(f' Joining the JinaD process')
        self.worker.join(*args, **kwargs)
        self.logger.debug(f' Successfully joined the JinaD process')

    def _terminate(self):
        """Terminate the Pea.
        This method calls :meth:`terminate` in :class:`threading.Thread` or :class:`multiprocesssing.Process`.
        """
        self.cancel_event.set()  # Inform JinaD Process to stop streaming
        if hasattr(self.worker, 'terminate'):
            self.logger.debug(f'terminating the JinaD Process')
            self.worker.terminate()
            self.logger.debug(f'JinaD Process properly terminated')

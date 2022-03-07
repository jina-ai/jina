import argparse
import asyncio
import copy
import multiprocessing
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Union

from jina.enums import replace_enum_to_str
from jina.excepts import (
    DaemonConnectivityError,
    DaemonPodCreationFailed,
    DaemonWorkspaceCreationFailed,
)
from jina.helper import run_async
from jina.importer import ImportExtensions
from jina.jaml.helper import complete_path
from jina.logging.logger import JinaLogger
from jina.orchestrate.pods import BasePod
from jina.orchestrate.pods.helper import _get_worker, is_ready

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
        envs: Optional[Dict] = None,
    ):
        """Method responsible to manage a remote Pod

        This method is the target for the Pod's `thread` or `process`

        .. note::
            Please note that env variables are process-specific. Subprocess inherits envs from
            the main process. But Subprocess's envs do NOT affect the main process. It does NOT
            mess up user local system envs.

        :param args: namespace args from the Pod
        :param is_started: concurrency event to communicate runtime is properly started. Used for better logging
        :param is_shutdown: concurrency event to communicate runtime is terminated
        :param is_ready: concurrency event to communicate runtime is ready to receive messages
        :param is_cancelled: concurrency event to receive cancelling signal from the Pod. Needed by some runtimes
        :param envs: a dictionary of environment variables to be passed to remote Pod
        """
        self.args = args
        self.envs = envs
        self.is_started = is_started
        self.is_shutdown = is_shutdown
        self.is_ready = is_ready
        self.is_cancelled = is_cancelled
        self.pod_id = None
        self._logger = JinaLogger('RemotePod', **vars(args))
        run_async(self._run)

    async def _run(self):
        """Manage a remote Pod"""
        try:
            await self._create_remote_pod()
        except Exception as ex:
            self._logger.error(
                f'{ex!r} while starting a remote Pod'
                + f'\n add "--quiet-error" to suppress the exception details'
                if not self.args.quiet_error
                else '',
                exc_info=not self.args.quiet_error,
            )
        else:
            self.is_started.set()
            self.is_ready.set()
            await self._wait_until_cancelled()
        finally:
            await self._terminate_remote_pod()
            self.is_shutdown.set()
            self._logger.debug('JinaDProcessTarget terminated')

    async def _create_remote_pod(self):
        """Create Workspace, Pod on remote JinaD server"""
        with ImportExtensions(required=True):
            # rich & aiohttp are used in `AsyncJinaDClient`
            import aiohttp
            import rich

            from daemon.clients import AsyncJinaDClient

            assert rich
            assert aiohttp

        # NOTE: args.timeout_ready is always set to -1 for JinadRuntime so that wait_for_success doesn't fail in Pod,
        # so it can't be used for Client timeout.
        self.client = AsyncJinaDClient(
            host=self.args.host, port=self.args.port_jinad, logger=self._logger
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
            self._logger.critical(f'remote workspace creation failed')
            raise DaemonWorkspaceCreationFailed

        payload = replace_enum_to_str(vars(self._mask_args()))
        # Create a remote Pod in the above workspace
        success, response = await self.client.pods.create(
            workspace_id=workspace_id, payload=payload, envs=self.envs
        )
        if not success:
            self._logger.critical(f'remote pod creation failed')
            raise DaemonPodCreationFailed(response)
        else:
            self.pod_id = response

    async def _sleep_forever(self):
        """Sleep forever, no prince will come."""
        await asyncio.sleep(1e10)

    async def _wait_until_cancelled(self):
        while not self.is_cancelled.is_set():
            await asyncio.sleep(0.1)

    async def _terminate_remote_pod(self):
        """Removes the remote Pod"""
        if self.pod_id is not None:
            if await self.client.pods.delete(id=self.pod_id):
                self._logger.success(
                    f'Successfully terminated remote Pod {self.pod_id}'
                )
            # Don't delete workspace here, as other Executors might use them.
            # TODO(Deepankar): probably enable an arg here?

    @property
    def filepaths(self) -> List[Path]:
        """Get file/directories to be uploaded to remote workspace

        :return: filepaths to be uploaded to remote
        """
        paths = set()
        if not self.args.upload_files:
            self._logger.warning(f'no files passed to upload to remote')
        else:
            for path in self.args.upload_files:
                try:
                    fullpath = Path(complete_path(path))
                    paths.add(fullpath)
                except FileNotFoundError:
                    self._logger.error(f'invalid path {path} passed')

        return list(paths)

    def _mask_args(self):
        cargs = copy.deepcopy(self.args)

        # TODO:/NOTE this prevents jumping from remote to another remote (Han: 2021.1.17)
        from jina import __default_host__

        cargs.host = __default_host__
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
            self._logger.debug('\n'.join(changes))

        return cargs


class JinaDPod(BasePod):
    """Manages a remote Pod by handling a separate Process / Thread"""

    def __init__(self, args: 'argparse.Namespace'):
        super().__init__(args)
        self.worker = _get_worker(
            args=args,
            target=JinaDProcessTarget(),
            kwargs={
                'args': args,
                'envs': self._envs,
                'is_started': self.is_started,
                'is_shutdown': self.is_shutdown,
                'is_ready': self.is_ready,
                'is_cancelled': self.cancel_event,
            },
        )

    def _wait_for_ready_or_shutdown(self, timeout: Optional[float]):
        """
        Waits for the process to be ready or to know it has failed.

        :param timeout: The time to wait before readiness or failure is determined
            .. # noqa: DAR201
        """
        is_ready_or_shutdown = self.wait_for_ready_or_shutdown(
            timeout=timeout,
            ready_or_shutdown_event=self.ready_or_shutdown.event,
            ctrl_address=self.runtime_ctrl_address,
            timeout_ctrl=self._timeout_ctrl,
        )
        if is_ready_or_shutdown:
            is_ready_or_shutdown = is_ready(self.runtime_ctrl_address)
        return is_ready_or_shutdown

    @staticmethod
    def wait_for_ready_or_shutdown(
        timeout: Optional[float],
        ready_or_shutdown_event: Union['multiprocessing.Event', 'threading.Event'],
        ctrl_address: str,
        **kwargs,
    ):
        """
        Check if the runtime has successfully started

        :param timeout: The time to wait before readiness or failure is determined
        :param ctrl_address: the address where the control message needs to be sent
        :param ready_or_shutdown_event: the multiprocessing event to detect if the process failed or is ready
        :param kwargs: extra keyword arguments
        :return: True if is ready or it needs to be shutdown
        """
        import time

        timeout_ns = 1000000000 * timeout if timeout else None
        now = time.time_ns()
        while timeout_ns is None or time.time_ns() - now < timeout_ns:
            # is_ready returns True is the Pod is actually created by JinaD
            # ready_or_shutdown_event is set after JinaDProcessTarget
            if ready_or_shutdown_event.is_set():
                return True
            time.sleep(0.1)
        return False

    def start(self):
        """Start the JinaD Process (to manage remote Pod).
        .. #noqa: DAR201
        """
        self.worker.start()
        if not self.args.noblock_on_start:
            self.wait_start_success()
        return self

    def join(self, *args, **kwargs):
        """Joins the Pod.
        This method calls :meth:`join` in :class:`threading.Thread` or :class:`multiprocesssing.Process`.

        :param args: extra positional arguments to pass to join
        :param kwargs: extra keyword arguments to pass to join
        """
        self.logger.debug(f' Joining the JinaD process')
        self.worker.join(*args, **kwargs)
        self.logger.debug(f' Successfully joined the JinaD process')

    def _terminate(self):
        """Terminate the Pod.
        This method calls :meth:`terminate` in :class:`threading.Thread` or :class:`multiprocesssing.Process`.
        """
        self.cancel_event.set()  # Inform JinaD Process to stop streaming
        self.is_shutdown.wait()  # Wait until JinaD terminates remote Pod and sets shutdown event
        if hasattr(self.worker, 'terminate'):
            self.logger.debug(f'terminating the JinaD Process')
            self.worker.terminate()
            self.logger.debug(f'JinaD Process properly terminated')

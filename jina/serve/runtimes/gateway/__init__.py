import argparse
import urllib
from abc import ABC
from http import HTTPStatus
from typing import TYPE_CHECKING, Optional, Union

from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime

if TYPE_CHECKING:
    import asyncio
    import multiprocessing
    import threading


class GatewayRuntime(AsyncNewLoopRuntime, ABC):
    """
    The Runtime from which the GatewayRuntimes need to inherit
    """

    def __init__(
        self,
        args: argparse.Namespace,
        cancel_event: Optional[
            Union['asyncio.Event', 'multiprocessing.Event', 'threading.Event']
        ] = None,
        **kwargs,
    ):
        # this order is intentional: The timeout is needed in _create_topology_graph(), called by super
        self.timeout_send = args.timeout_send
        if self.timeout_send:
            self.timeout_send /= 1e3  # convert ms to seconds
        super().__init__(args, cancel_event, **kwargs)

    @staticmethod
    def is_ready(ctrl_address: str, protocol: Optional[str] = 'grpc', **kwargs) -> bool:
        """
        Check if status is ready.

        :param ctrl_address: the address where the control request needs to be sent
        :param protocol: protocol of the gateway runtime
        :param kwargs: extra keyword arguments

        :return: True if status is ready else False.
        """

        if protocol is None or protocol == 'grpc':
            res = AsyncNewLoopRuntime.is_ready(ctrl_address)
        else:
            try:
                conn = urllib.request.urlopen(url=f'http://{ctrl_address}')
                res = conn.code == HTTPStatus.OK
            except:
                res = False
        return res

    @classmethod
    def wait_for_ready_or_shutdown(
        cls,
        timeout: Optional[float],
        ready_or_shutdown_event: Union['multiprocessing.Event', 'threading.Event'],
        ctrl_address: str,
        protocol: Optional[str] = 'grpc',
        **kwargs,
    ):
        """
        Check if the runtime has successfully started

        :param timeout: The time to wait before readiness or failure is determined
        :param ctrl_address: the address where the control message needs to be sent
        :param ready_or_shutdown_event: the multiprocessing event to detect if the process failed or is ready
        :param protocol: protocol of the gateway runtime
        :param kwargs: extra keyword arguments

        :return: True if is ready or it needs to be shutdown
        """
        return super().wait_for_ready_or_shutdown(
            timeout=timeout,
            ready_or_shutdown_event=ready_or_shutdown_event,
            ctrl_address=ctrl_address,
            protocol=protocol,
        )

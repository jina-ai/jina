from abc import ABC
from contextlib import ExitStack

from rich.table import Table

from jina.helper import CatchAllCleanupContextManager, get_internal_ip, get_public_ip


class BaseOrchestrator(ExitStack, ABC):
    """Base orchestrator class"""

    def __enter__(self):
        with CatchAllCleanupContextManager(self):
            return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, '_stop_event'):
            self._stop_event.set()

        super().__exit__(exc_type, exc_val, exc_tb)

    def _init_table(self):
        table = Table(
            title=None, box=None, highlight=True, show_header=False, min_width=40
        )
        table.add_column('', justify='left')
        table.add_column('', justify='right')
        table.add_column('', justify='right')
        return table

    @property
    def address_private(self) -> str:
        """Return the private IP address of the gateway for connecting from other machine in the same network


        .. # noqa: DAR201"""
        if getattr(self, '_internal_ip', None):
            return self._internal_ip
        else:
            self._internal_ip = get_internal_ip()
        return self._internal_ip

    @property
    def address_public(self) -> str:
        """Return the public IP address of the gateway for connecting from other machine in the public network


        .. # noqa: DAR201"""
        if getattr(self, '_public_ip', None):
            return self._public_ip
        else:
            self._public_ip = get_public_ip()
        return self._public_ip

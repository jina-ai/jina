from typing import Iterable

from jina.executors.indexers import BaseIndexer


class BaseQueryIndexer(BaseIndexer):
    """An indexer only for querying. It only reads once (at creation time, from a dump)"""

    def load_dump(self, dump_path):
        """Load the dump at the dump_path

        :param dump_path: the path of the dump"""
        raise NotImplementedError

    def _log_warn(self):
        self.logger.error(f'Index {self.__class__} is write-once')

    def add(
        self, keys: Iterable[str], values: Iterable[bytes], *args, **kwargs
    ) -> None:
        """Disabled. QueryIndexers are write-once (at instantiation time)


        .. # noqa: DAR101
        """
        self._log_warn()

    def update(
        self, keys: Iterable[str], values: Iterable[bytes], *args, **kwargs
    ) -> None:
        """Disabled. QueryIndexers are write-once (at instantiation time)


        .. # noqa: DAR101
        """
        self._log_warn()

    def delete(self, keys: Iterable[str], *args, **kwargs) -> None:
        """Disabled. QueryIndexers are write-once (at instantiation time)


        .. # noqa: DAR101
        """
        self._log_warn()

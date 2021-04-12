from typing import Iterable, Optional, Dict

from jina.executors.indexers import BaseIndexer


class BaseQueryIndexer(BaseIndexer):
    """An indexer only for querying. It only reads once (at creation time, from a dump)"""

    def _post_init_wrapper(
        self,
        _metas: Optional[Dict] = None,
        _requests: Optional[Dict] = None,
        fill_in_metas: bool = True,
    ) -> None:
        super()._post_init_wrapper(_metas, _requests, fill_in_metas)
        self.dump_path = _metas.get('dump_path')
        # TODO this shouldn't be required
        # we don't do this for Compounds, as the _components
        # are not yet set at this stage.
        # for Compound we use a `_post_components`
        if self.dump_path and not hasattr(self, 'components'):
            self._load_dump(self.dump_path)

    def _load_dump(self, dump_path):
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

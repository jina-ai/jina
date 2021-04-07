from typing import Optional, Dict

from jina.executors.compound import CompoundExecutor
from jina.executors.indexers.query import BaseQueryIndexer


class QueryCompoundExecutor(CompoundExecutor, BaseQueryIndexer):
    """A Compound Executor that wraps several QueryIndexers

    :param dump_path: the path to initialize from
    """

    def _post_init_wrapper(
        self,
        _metas: Optional[Dict] = None,
        _requests: Optional[Dict] = None,
        fill_in_metas: bool = True,
    ) -> None:
        super()._post_init_wrapper(_metas, _requests, fill_in_metas)
        self.dump_path = _metas.get('dump_path')

    def _post_components(self):
        print(f'### {self=} would call load dump. {self.components=}')
        self.load_dump(self.dump_path)

    def load_dump(self, dump_path, *args, **kwargs):
        """Loads the data in the indexer

        :param dump_path: the path to the dump
        :param args: passed to the inner Indexer's load_dump
        :param kwargs: passed to the inner Indexer's load_dump
        """
        for c in self.components:
            c.load_dump(dump_path)

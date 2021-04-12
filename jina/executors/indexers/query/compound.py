from jina.executors.compound import CompoundExecutor
from jina.executors.indexers.query import BaseQueryIndexer


class CompoundQueryExecutor(CompoundExecutor, BaseQueryIndexer):
    """A Compound Executor that wraps several QueryIndexers

    :param dump_path: the path to initialize from
    """

    # TODO this shouldn't be required
    # we don't do this for Compounds, as the _components
    # are not yet set at this stage.
    # for Compound we use a `_post_components`
    def _post_components(self):
        self._load_dump(self.dump_path)

    def _load_dump(self, dump_path, *args, **kwargs):
        """Loads the data in the indexer

        :param dump_path: the path to the dump
        :param args: passed to the inner Indexer's load_dump
        :param kwargs: passed to the inner Indexer's load_dump
        """
        for c in self.components:
            c._load_dump(dump_path)


class CompoundQueryIndexer(CompoundQueryExecutor):
    """Alias"""

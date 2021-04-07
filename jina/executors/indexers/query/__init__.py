from jina.executors.indexers import BaseIndexer


class BaseQueryIndexer(BaseIndexer):
    """An indexer only for querying. It only reads once (at creation time)"""

    def load_dump(self, dump_path):
        """Load the dump at the dump_path

        :param dump_path: the path of the dump"""
        raise NotImplementedError

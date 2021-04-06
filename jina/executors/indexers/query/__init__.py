from jina.executors.indexers import BaseIndexer


class BaseQueryIndexer(BaseIndexer):
    """An indexer only for querying. It only reads once (at creation time)"""

    def load_dump(self, path):
        """Load the dump at the path

        :param path: the path of the dump"""
        raise NotImplementedError

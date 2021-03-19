from jina.executors import BaseExecutor
from jina.executors.compound import CompoundExecutor


class QueryBaseExecutor(BaseExecutor):
    """TODO"""

    def import_uri_path(self, path):
        """TODO

        :param path:
        """
        raise NotImplementedError


class QueryCompoundExecutor(CompoundExecutor, QueryBaseExecutor):
    """TODO"""

    def import_uri_path(self, path):
        """TODO

        :param path:
        """
        for c in self.components:
            c.import_uri_path(path)

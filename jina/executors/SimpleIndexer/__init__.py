import os
from typing import Optional, Any

from .. import BaseExecutor
from ...helper import call_obj_fn, cached_property, get_readable_size
from ...logging import JinaLogger


class BaseIndexer(BaseExecutor):

    def __init__(self, index_filename: Optional[str] = None, key_length: int = 36, **kwargs):
        super().__init__(**kwargs)
        self.index_filename = (
                index_filename or self.metas.name  #: the file name of the stored index, no path is required
        )
        self.logger = JinaLogger(self.metas.name or self.__class__.__name__)
        self.key_length = key_length  #: the default minimum length of the key, will be expanded one time on the first batch
        self._size = 0
        self.handler_mutex = True  #: only one handler at a time by default
        self.is_handler_loaded = False

    @property
    def index_abspath(self) -> str:
        """
        Get the file path of the index storage
        :return: absolute path
        """
        return os.path.join(self.workspace, self.index_filename)

    @cached_property
    def query_handler(self):
        """A readable and indexable object, could be dict, map, list, numpy array etc.
        :return: read handler
        .. note::
            :attr:`query_handler` and :attr:`write_handler` are by default mutex
        """
        r = None
        if not self.handler_mutex or not self.is_handler_loaded:
            r = self.get_query_handler()
            if r is None:
                self.logger.warning(
                    f'you can not query from {self} as its "query_handler" is not set. '
                    'If you are indexing data from scratch then it is fine. '
                    'If you are querying data then the index file must be empty or broken.'
                )
            else:
                self.logger.info(f'indexer size: {self.size}')
                self.is_handler_loaded = True
        if r is None:
            r = self.null_query_handler
        return r

    @cached_property
    def null_query_handler(self) -> Optional[Any]:
        """The empty query handler when :meth:`get_query_handler` fails
        :return: nothing
        """
        return

    @property
    def is_exist(self) -> bool:
        """
        Check if the database is exist or not
        :return: true if the absolute index path exists, else false
        """
        return os.path.exists(self.index_abspath)

    @cached_property
    def write_handler(self):
        """A writable and indexable object, could be dict, map, list, numpy array etc.
        :return: write handler
        .. note::
            :attr:`query_handler` and :attr:`write_handler` are by default mutex
        """

        # ! a || ( a && b )
        # =
        # ! a || b
        if not self.handler_mutex or not self.is_handler_loaded:
            r = self.get_add_handler() if self.is_exist else self.get_create_handler()

            if r is None:
                self.logger.warning(
                    '"write_handler" is None, you may not add data to this index, '
                    'unless "write_handler" is later assigned with a meaningful value'
                )
            else:
                self.is_handler_loaded = True
            return r

    def get_query_handler(self):
        """Get a *readable* index handler when the ``index_abspath`` already exist, need to be overridden"""
        raise NotImplementedError

    def get_add_handler(self):
        """Get a *writable* index handler when the ``index_abspath`` already exist, need to be overridden"""
        raise NotImplementedError

    def get_create_handler(self):
        """Get a *writable* index handler when the ``index_abspath`` does not exist, need to be overridden"""
        raise NotImplementedError

    @property
    def size(self) -> int:
        """
        The number of vectors or documents indexed.
        :return: size
        """
        return self._size

    def close(self):
        """Close all file-handlers and release all resources. """
        self.logger.info(
            f'indexer size: {self.size} physical size: {get_readable_size(self.physical_size)}'
        )
        self.flush()
        call_obj_fn(self.write_handler, 'close')
        call_obj_fn(self.query_handler, 'close')
        super().close()

    def flush(self):
        """Flush all buffered data to ``index_abspath`` """
        try:
            # It may have already been closed by the Pea using context manager
            call_obj_fn(self.write_handler, 'flush')
        except:
            pass


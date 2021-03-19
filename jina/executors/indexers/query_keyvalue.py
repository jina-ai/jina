import mmap
import os
import time
from typing import Optional, Union

import numpy as np

from . import BaseKVIndexer
from .keyvalue import BinaryPbIndexer
from .vector import BaseNumpyIndexer
from ..reload_helpers import DumpPersistor

HEADER_NONE_ENTRY = (-1, -1, -1)
TIME_WAIT_SWITCH = 5


class QueryBinaryPbIndexer(BaseKVIndexer):
    """Simple Key-value indexer."""

    def __init(self):
        self.preparing = False

    class DumpReadHandler(BinaryPbIndexer.ReadHandler):
        # TODO
        pass

    def reload(self, path):
        print(f'## reload of QueryBinaryPb')
        data = DumpPersistor.import_dump(path, 'all')
        # func to prepare new state
        if not self.preparing:
            self.preparing = True
            self.prepare(data)
            self.preparing = False
        return

    def prepare(self, data):
        self.tmp_vec_idxer = BinaryPbIndexer(
            delete_on_dump=self.delete_on_dump,
            workspace=os.path.join(self._workspace, 'new_workspace_for_preparation'),
        )
        self.tmp_vec_idxer.add(*data)
        self.tmp_vec_idxer.save(
            os.path.join(self._workspace, 'new_workspace_for_preparation')
        )

    def switch(self, data, new_path):
        old_q_handler = self.query_handler
        # del self.query_handler WAIT FOR PR
        self.__dict__['CACHED_query_handler'] = self.next_state
        old_q_handler.close()
        self.next_state = None
        self.preparing = False

    class WriteHandler:
        """
        Write file handler.

        :param path: Path of the file.
        :param mode: Writing mode. (e.g. 'ab', 'wb')
        """

        def __init__(self, path, mode):
            self.body = open(path, mode)
            self.header = open(path + '.head', mode)

        def close(self):
            """Close the file."""
            self.body.close()
            self.header.close()

        def flush(self):
            """Clear the body and header."""
            self.body.flush()
            self.header.flush()

    class ReadHandler:
        """
        Read file handler.

        :param path: Path of the file.
        :param key_length: Length of key.
        """

        def __init__(self, path, key_length):
            with open(path + '.head', 'rb') as fp:
                tmp = np.frombuffer(
                    fp.read(),
                    dtype=[
                        ('', (np.str_, key_length)),
                        ('', np.int64),
                        ('', np.int64),
                        ('', np.int64),
                    ],
                )
                self.header = {
                    r[0]: None
                    if np.array_equal((r[1], r[2], r[3]), HEADER_NONE_ENTRY)
                    else (r[1], r[2], r[3])
                    for r in tmp
                }
            self._body = open(path, 'r+b')
            self.body = self._body.fileno()

        def close(self):
            """Close the file."""
            self._body.close()

    def __getstate__(self):
        # called on pickle save
        if self.delete_on_dump:
            self._delete_invalid_indices()
        d = super().__getstate__()
        return d

    def _delete_invalid_indices(self):
        if self.query_handler:
            self.query_handler.close()
        if self.write_handler:
            self.write_handler.flush()
            self.write_handler.close()

        keys = []
        vals = []
        # we read the valid values and write them to the intermediary file
        read_handler = self.ReadHandler(self.index_abspath, self.key_length)
        for key in read_handler.header.keys():
            pos_info = read_handler.header.get(key, None)
            if pos_info:
                p, r, l = pos_info
                with mmap.mmap(read_handler.body, offset=p, length=l) as m:
                    keys.append(key)
                    vals.append(m[r:])
        read_handler.close()
        if len(keys) == 0:
            return

        # intermediary file
        tmp_file = self.index_abspath + '-tmp'
        self._start = 0
        filtered_data_writer = self.WriteHandler(tmp_file, 'ab')
        # reset size
        self._size = 0
        self._add(keys, vals, filtered_data_writer)
        filtered_data_writer.close()

        # replace orig. file
        # and .head file
        head_path = self.index_abspath + '.head'
        os.remove(self.index_abspath)
        os.remove(head_path)
        os.rename(tmp_file, self.index_abspath)
        os.rename(tmp_file + '.head', head_path)

    def get_add_handler(self) -> 'WriteHandler':
        """
        Get write file handler.

        :return: write handler
        """
        # keep _start position as in pickle serialization
        return self.WriteHandler(self.index_abspath, 'ab')

    def get_create_handler(self) -> 'WriteHandler':
        """
        Get write file handler.

        :return: write handler.
        """
        self._start = 0  # override _start position
        return self.WriteHandler(self.index_abspath, 'wb')

    def get_query_handler(self) -> 'ReadHandler':
        """
        Get read file handler.

        :return: read handler.
        """
        return self.ReadHandler(self.index_abspath, self.key_length)

    def __init__(
        self, delete_on_dump: bool = False, time_wait_switch=5, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._start = 0
        self._page_size = mmap.ALLOCATIONGRANULARITY
        self.delete_on_dump = delete_on_dump
        self.time_wait_switch = time_wait_switch

    def query(self, key: str) -> Optional[bytes]:
        """Find the serialized document to the index via document id.

        :param key: document id
        :return: serialized documents
        """
        q_handler = self.query_handler
        pos_info = q_handler.header.get(key, None)
        if pos_info is not None:
            p, r, l = pos_info
            with mmap.mmap(q_handler.body, offset=p, length=l) as m:
                return m[r:]

__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Optional

import numpy as np

from .vector import NumpyIndexer
from ...helper import cached_property


class MmapNumpyIndexer(NumpyIndexer):
    """:class:`BaseNumpyIndexer` stores and loads vector in a compresses binary file """

    batch_size = 512

    def get_add_handler(self):
        """Open a binary gzip file for adding new vectors

        :return: a file stream
        """
        return open(self.index_abspath, 'ab')

    def get_create_handler(self):
        """Create a new gzip file for adding new vectors

        :return: a file stream
        """
        return open(self.index_abspath, 'wb')

    @cached_property
    def raw_ndarray(self) -> Optional['np.ndarray']:
        return np.memmap(self.index_abspath, dtype=self.dtype, mode='r', shape=(self._size, self.num_dim))

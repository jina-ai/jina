__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import gzip
from os import path
from typing import Optional

import numpy as np

from .. import BaseVectorIndexer


class BaseNumpyIndexer(BaseVectorIndexer):
    """:class:`BaseNumpyIndexer` stores and loads vector in a compresses binary file """

    def __init__(self,
                 compress_level: int = 1,
                 ref_indexer: 'BaseNumpyIndexer' = None,
                 *args, **kwargs):
        """
        :param compress_level: The compresslevel argument is an integer from 0 to 9 controlling the
                        level of compression; 1 is fastest and produces the least compression,
                        and 9 is slowest and produces the most compression. 0 is no compression
                        at all. The default is 9.
        :param ref_indexer: Bootstrap the current indexer from a ``ref_indexer``. This enables user to switch
                            the query algorithm at the query time.

        """
        super().__init__(*args, **kwargs)
        self.num_dim = None
        self.dtype = None
        self.compress_level = compress_level
        self.key_bytes = b''
        self.key_dtype = None
        self._raw_ndarray = None
        self._ref_index_abspath = None

        if ref_indexer:
            # copy the header info of the binary file
            self.num_dim = ref_indexer.num_dim
            self.dtype = ref_indexer.dtype
            self.compress_level = ref_indexer.compress_level
            self.key_bytes = ref_indexer.key_bytes
            self.key_dtype = ref_indexer.key_dtype
            self._size = ref_indexer._size
            # point to the ref_indexer.index_filename
            # so that later in `post_init()` it will load from the referred index_filename
            self._ref_index_abspath = ref_indexer.index_abspath

    @property
    def index_abspath(self) -> str:
        """Get the file path of the index storage

        Use index_abspath

        """
        return getattr(self, '_ref_index_abspath', None) or self.get_file_from_workspace(self.index_filename)

    def get_add_handler(self):
        """Open a binary gzip file for adding new vectors

        :return: a gzip file stream
        """
        return gzip.open(self.index_abspath, 'ab', compresslevel=self.compress_level)

    def get_create_handler(self):
        """Create a new gzip file for adding new vectors

        :return: a gzip file stream
        """
        return gzip.open(self.index_abspath, 'wb', compresslevel=self.compress_level)

    def add(self, keys: 'np.ndarray', vectors: 'np.ndarray', *args, **kwargs):
        self._validate_key_vector_shapes(keys, vectors)
        self.write_handler.write(vectors.tobytes())
        self.key_bytes += keys.tobytes()
        self.key_dtype = keys.dtype.name
        self._size += keys.shape[0]

    def get_query_handler(self) -> Optional['np.ndarray']:
        """Open a gzip file and load it as a numpy ndarray

        :return: a numpy ndarray of vectors
        """
        vecs = self.raw_ndarray
        if vecs is not None:
            return self.build_advanced_index(vecs)
        else:
            return None

    def build_advanced_index(self, vecs: 'np.ndarray'):
        raise NotImplementedError

    def _load_gzip(self, abspath):
        self.logger.info(f'loading index from {abspath}...')
        if not path.exists(abspath):
            self.logger.warning('numpy data not found: {}'.format(abspath))
            return None
        result = None
        try:
            if self.num_dim and self.dtype:
                with gzip.open(abspath, 'rb') as fp:
                    result = np.frombuffer(fp.read(), dtype=self.dtype).reshape([-1, self.num_dim])
        except EOFError:
            self.logger.error(
                f'{abspath} is broken/incomplete, perhaps forgot to ".close()" in the last usage?')
        return result

    @property
    def raw_ndarray(self):
        if self._raw_ndarray is None:
            vecs = self._load_gzip(self.index_abspath)
            if vecs is None:
                return None

            if self.key_bytes and self.key_dtype:
                self.int2ext_key = np.frombuffer(self.key_bytes, dtype=self.key_dtype)

            if self.int2ext_key is not None and vecs is not None and vecs.ndim == 2:
                if self.int2ext_key.shape[0] != vecs.shape[0]:
                    self.logger.error(
                        f'the size of the keys and vectors are inconsistent ({self.int2ext_key.shape[0]} != {vecs.shape[0]}), '
                        f'did you write to this index twice? or did you forget to save indexer?')
                    return None
                if vecs.shape[0] == 0:
                    self.logger.warning(f'an empty index is loaded')

                self._raw_ndarray = vecs
                return self._raw_ndarray
            else:
                return None
        else:
            return self._raw_ndarray

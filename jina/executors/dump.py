import os
import sys
from typing import Iterable, Tuple

import numpy as np

from jina.enums import BetterEnum


class DumpTypes(BetterEnum):
    """The enum of dump formats"""

    DEFAULT = 0
    NUMPY = 1


BYTE_PADDING = 4


class DumpPersistor:
    """
    Class for creating and importing from dumps

    Do NOT instantiate. Only provides static methods
    """

    @staticmethod
    def export_dump_streaming(
        path: str,
        shards: int,
        size: int,
        data: Iterable[Tuple[str, np.array, bytes]],
    ):
        """Export the data to a path, based on sharding,

        :param path: path to dump
        :param shards: the nr of shards this pea is part of
        :param size: total amount of entries
        :param data: the generator of the data (ids, vectors, metadata)
        """
        if os.path.exists(path):
            raise Exception(f'path for dump {path} already exists. Not dumping...')
        size_per_shard = size // shards
        extra = size % shards
        # +1 because pea ids start at 1 when shards > 1
        # see jina/peapods/pods/helper.py:20
        shard_range = range(1, shards + 1) if shards > 1 else range(shards)
        shard_range = list(shard_range)
        for shard_id in shard_range:
            if shard_id == shard_range[-1]:
                size_this_shard = size_per_shard + extra
            else:
                size_this_shard = size_per_shard
            shard_path = os.path.join(path, str(shard_id))
            shard_written = 0
            os.makedirs(shard_path)
            vectors_fh, metas_fh, ids_fh = DumpPersistor._get_file_handlers(shard_path)
            while shard_written < size_this_shard:
                id_, vec, meta = next(data)
                vec_bytes = vec.tobytes()
                vectors_fh.write(
                    len(vec_bytes).to_bytes(BYTE_PADDING, sys.byteorder) + vec_bytes
                )
                metas_fh.write(len(meta).to_bytes(BYTE_PADDING, sys.byteorder) + meta)
                ids_fh.write(id_ + '\n')
                shard_written += 1
            vectors_fh.close()
            metas_fh.close()
            ids_fh.close()

    @staticmethod
    def import_vectors(path: str, pea_id: str):
        """Import id and vectors

        :param path: the path to the dump
        :param pea_id: the id of the pea (as part of the shards)
        :return:
        """
        path = os.path.join(path, pea_id)
        ids_gen = DumpPersistor._ids_gen(path)
        vecs_gen = DumpPersistor._vecs_gen(path)
        return ids_gen, vecs_gen

    @staticmethod
    def import_metas(path: str, pea_id: str):
        """Import id and metadata

        :param path: the path of the dump
        :param pea_id: the id of the pea (as part of the shards)
        :return:
        """
        path = os.path.join(path, pea_id)
        ids_gen = DumpPersistor._ids_gen(path)
        metas_gen = DumpPersistor._metas_gen(path)
        return ids_gen, metas_gen

    @staticmethod
    def _ids_gen(path):
        with open(os.path.join(path, 'ids'), 'r') as ids_fh:
            for l in ids_fh:
                yield l.strip()

    @staticmethod
    def _vecs_gen(path):
        with open(os.path.join(path, 'vectors'), 'rb') as vectors_fh:
            while True:
                next_size = vectors_fh.read(BYTE_PADDING)
                next_size = int.from_bytes(next_size, byteorder=sys.byteorder)
                if next_size:
                    vec = np.frombuffer(
                        vectors_fh.read(next_size),
                        dtype=np.float64,
                    )
                    yield vec
                else:
                    break

    @staticmethod
    def _metas_gen(path):
        with open(os.path.join(path, 'metas'), 'rb') as metas_fh:
            while True:
                next_size = metas_fh.read(BYTE_PADDING)
                next_size = int.from_bytes(next_size, byteorder=sys.byteorder)
                if next_size:
                    meta = metas_fh.read(next_size)
                    yield meta
                else:
                    break

    @staticmethod
    def _get_file_handlers(shard_path):
        vectors_fh = open(os.path.join(shard_path, 'vectors'), 'wb')
        metas_fh = open(os.path.join(shard_path, 'metas'), 'wb')
        ids_fh = open(os.path.join(shard_path, 'ids'), 'w')
        return vectors_fh, metas_fh, ids_fh

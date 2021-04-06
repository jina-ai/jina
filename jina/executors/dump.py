import os
import sys
from typing import Iterable, Tuple, List

import numpy as np

from jina.enums import BetterEnum

BYTE_PADDING = 4


class DumpTypes(BetterEnum):
    """The enum of dump formats"""

    DEFAULT = 0


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
        formats: List[DumpTypes],
    ):
        """Export the data to a path, based on sharding,

        :param path: path to dump
        :param shards: the nr of shards this pea is part of
        :param size: total amount of entries
        :param data: the generator of the data (ids, vectors, metadata)
        :param formats: the list of formats in which we dump
        """
        for format in formats:
            if format == DumpTypes.DEFAULT:
                DumpPersistor._handle_dump(data, path, shards, size)
            else:
                raise NotImplementedError('Not other format types supported right now')

    @staticmethod
    def _handle_dump(data, path, shards, size):
        if os.path.exists(path):
            raise Exception(f'path for dump {path} already exists. Not dumping...')
        size_per_shard = size // shards
        extra = size % shards
        shard_range = list(range(shards))
        for shard_id in shard_range:
            if shard_id == shard_range[-1]:
                size_this_shard = size_per_shard + extra
            else:
                size_this_shard = size_per_shard
            DumpPersistor._write_shard_data(data, path, shard_id, size_this_shard)

    @staticmethod
    def _write_shard_data(data, path, shard_id, size_this_shard):
        shard_path = os.path.join(path, str(shard_id))
        shard_docs_written = 0
        os.makedirs(shard_path)
        vectors_fp, metas_fp, ids_fp = DumpPersistor._get_file_paths(shard_path)
        with open(vectors_fp, 'wb') as vectors_fh:
            with open(metas_fp, 'wb') as metas_fh:
                with open(ids_fp, 'w') as ids_fh:
                    while shard_docs_written < size_this_shard:
                        id_, vec, meta = next(data)
                        vec_bytes = vec.tobytes()
                        vectors_fh.write(
                            len(vec_bytes).to_bytes(BYTE_PADDING, sys.byteorder)
                            + vec_bytes
                        )
                        metas_fh.write(
                            len(meta).to_bytes(BYTE_PADDING, sys.byteorder) + meta
                        )
                        ids_fh.write(id_ + '\n')
                        shard_docs_written += 1

    @staticmethod
    def import_vectors(path: str, pea_id: str):
        """Import id and vectors

        :param path: the path to the dump
        :param pea_id: the id of the pea (as part of the shards)
        :return: the generators for the ids and for the vectors
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
        :return: the generators for the ids and for the metadata
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
    def _get_file_paths(shard_path):
        vectors_fp = os.path.join(shard_path, 'vectors')
        metas_fp = os.path.join(shard_path, 'metas')
        ids_fp = os.path.join(shard_path, 'ids')
        return vectors_fp, metas_fp, ids_fp

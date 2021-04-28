import os
import sys
from typing import Tuple, Generator, BinaryIO, TextIO

import numpy as np

BYTE_PADDING = 4


def export_dump_streaming(
    path: str,
    shards: int,
    size: int,
    data: Generator[Tuple[str, np.array, bytes], None, None],
):
    """Export the data to a path, based on sharding,

    :param path: path to dump
    :param shards: the nr of shards this pea is part of
    :param size: total amount of entries
    :param data: the generator of the data (ids, vectors, metadata)
    """
    _handle_dump(data, path, shards, size)


def _handle_dump(
    data: Generator[Tuple[str, np.array, bytes], None, None],
    path: str,
    shards: int,
    size: int,
):
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
        _write_shard_data(data, path, shard_id, size_this_shard)


def _write_shard_data(
    data: Generator[Tuple[str, np.array, bytes], None, None],
    path: str,
    shard_id: int,
    size_this_shard: int,
):
    shard_path = os.path.join(path, str(shard_id))
    shard_docs_written = 0
    os.makedirs(shard_path)
    vectors_fp, metas_fp, ids_fp = _get_file_paths(shard_path)
    with open(vectors_fp, 'wb') as vectors_fh, open(metas_fp, 'wb') as metas_fh, open(
        ids_fp, 'w'
    ) as ids_fh:
        while shard_docs_written < size_this_shard:
            _write_shard_files(data, ids_fh, metas_fh, vectors_fh)
            shard_docs_written += 1


def _write_shard_files(
    data: Generator[Tuple[str, np.array, bytes], None, None],
    ids_fh: TextIO,
    metas_fh: BinaryIO,
    vectors_fh: BinaryIO,
):
    id_, vec, meta = next(data)
    vec_bytes = vec.tobytes()
    vectors_fh.write(len(vec_bytes).to_bytes(BYTE_PADDING, sys.byteorder) + vec_bytes)
    metas_fh.write(len(meta).to_bytes(BYTE_PADDING, sys.byteorder) + meta)
    ids_fh.write(id_ + '\n')


def import_vectors(path: str, pea_id: str):
    """Import id and vectors

    :param path: the path to the dump
    :param pea_id: the id of the pea (as part of the shards)
    :return: the generators for the ids and for the vectors
    """
    path = os.path.join(path, pea_id)
    ids_gen = _ids_gen(path)
    vecs_gen = _vecs_gen(path)
    return ids_gen, vecs_gen


def import_metas(path: str, pea_id: str):
    """Import id and metadata

    :param path: the path of the dump
    :param pea_id: the id of the pea (as part of the shards)
    :return: the generators for the ids and for the metadata
    """
    path = os.path.join(path, pea_id)
    ids_gen = _ids_gen(path)
    metas_gen = _metas_gen(path)
    return ids_gen, metas_gen


def _ids_gen(path: str):
    with open(os.path.join(path, 'ids'), 'r') as ids_fh:
        for l in ids_fh:
            yield l.strip()


def _vecs_gen(path: str):
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


def _metas_gen(path: str):
    with open(os.path.join(path, 'metas'), 'rb') as metas_fh:
        while True:
            next_size = metas_fh.read(BYTE_PADDING)
            next_size = int.from_bytes(next_size, byteorder=sys.byteorder)
            if next_size:
                meta = metas_fh.read(next_size)
                yield meta
            else:
                break


def _get_file_paths(shard_path: str):
    vectors_fp = os.path.join(shard_path, 'vectors')
    metas_fp = os.path.join(shard_path, 'metas')
    ids_fp = os.path.join(shard_path, 'ids')
    return vectors_fp, metas_fp, ids_fp

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
    @staticmethod
    def export_dump_streaming(
        path,
        data: Iterable[Tuple[str, np.array, bytes]],
    ):
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, 'vectors'), 'wb') as vectors_fh:
            with open(os.path.join(path, 'metas'), 'wb') as metas_fh:
                with open(os.path.join(path, 'ids'), 'w') as ids_fh:
                    for id_, vec, meta in data:
                        vec_bytes = vec.tobytes()
                        vectors_fh.write(
                            len(vec_bytes).to_bytes(BYTE_PADDING, sys.byteorder)
                            + vec_bytes
                        )
                        metas_fh.write(
                            len(meta).to_bytes(BYTE_PADDING, sys.byteorder) + meta
                        )
                        ids_fh.write(id_ + '\n')

    @staticmethod
    def import_vectors(path):
        ids_gen = DumpPersistor._ids_gen(path)
        vecs_gen = DumpPersistor._vecs_gen(path)
        return ids_gen, vecs_gen

    @staticmethod
    def import_metas(path):
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

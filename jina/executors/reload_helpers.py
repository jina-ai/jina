import os
import pickle
import sys
from typing import Union, Iterable, Tuple

import numpy as np

from jina.enums import BetterEnum

SYNC_MODE = True


class DumpTypes(BetterEnum):
    """The enum of dump formats"""

    DEFAULT = 0
    NUMPY = 1


BYTE_PADDING = 4


class DumpPersistor:
    @staticmethod
    def export_dump(path, data):
        # split into vectors and kv
        pickle.dump(data['ids'], open(os.path.join(path, 'ids.pkl'), 'wb'))
        pickle.dump(data['vectors'], open(os.path.join(path, 'vectors.pkl'), 'wb'))
        pickle.dump(data['kv'], open(os.path.join(path, 'kv.pkl'), 'wb'))

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
        # TODO
        pass

    @staticmethod
    def import_dump(path, content: Union['all', 'vector', 'kv']):
        # split into vectors and kv
        # TODO maybe split into separate functions based on 'content'
        if content == 'vector':
            return [['id1', 'id2', 'id3'], np.ones([3, 7])]
        elif content == 'kv':
            return [
                ['id1', 'id2', 'id3'],
                [
                    {
                        'id': 'id1',
                        'text': 'our text 1',
                        'embedding': np.ones(
                            [
                                7,
                            ]
                        ),
                    },
                    {
                        'id': 'id2',
                        'text': 'our text 2',
                        'embedding': np.zeros(
                            [
                                7,
                            ]
                        ),
                    },
                    {
                        'id': 'id3',
                        'text': 'our text 3',
                        'embedding': np.zeros(
                            [
                                7,
                            ]
                        ),
                    },
                ],
            ]

    @classmethod
    def _ids_gen(cls, path):
        with open(os.path.join(path, 'ids'), 'r') as ids_fh:
            for l in ids_fh:
                yield l.strip()

    @classmethod
    def _vecs_gen(cls, path):
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

import os
import sys
from typing import Iterator, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from docarray import Document

file_dir = os.path.dirname(__file__)
sys.path.append(os.path.dirname(file_dir))


def random_docs(
    num_docs,
    chunks_per_doc=5,
    embed_dim=10,
    jitter=1,
    start_id=0,
    embedding=True,
    sparse_embedding=False,
    text='hello world',
) -> Iterator['Document']:
    from docarray import Document

    next_chunk_doc_id = start_id + num_docs
    for j in range(num_docs):
        doc_id = str(start_id + j)

        d = Document(id=doc_id)
        d.text = text
        d.tags['id'] = doc_id
        if embedding:
            if sparse_embedding:
                from scipy.sparse import coo_matrix

                d.embedding = coo_matrix(
                    (np.array([1, 1, 1]), (np.array([0, 1, 2]), np.array([1, 2, 1])))
                )
            else:
                d.embedding = np.random.random(
                    [embed_dim + np.random.randint(0, jitter)]
                )

        for _ in range(chunks_per_doc):
            chunk_doc_id = str(next_chunk_doc_id)

            c = Document(id=chunk_doc_id)
            c.text = 'i\'m chunk %s from doc %s' % (chunk_doc_id, doc_id)
            if embedding:
                c.embedding = np.random.random(
                    [embed_dim + np.random.randint(0, jitter)]
                )
            c.tags['parent_id'] = doc_id
            c.tags['id'] = chunk_doc_id
            d.chunks.append(c)
            next_chunk_doc_id += 1

        yield d


def validate_callback(mock, validate_func):
    for args, kwargs in mock.call_args_list:
        validate_func(*args, **kwargs)

    mock.assert_called()

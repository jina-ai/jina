import os
import sys
import shutil
from typing import Iterator

import numpy as np

from jina import Document

file_dir = os.path.dirname(__file__)
sys.path.append(os.path.dirname(file_dir))


def random_docs(num_docs, chunks_per_doc=5, embed_dim=10, jitter=1, start_id=0, embedding=True) -> Iterator['Document']:
    next_chunk_doc_id = start_id + num_docs
    for j in range(num_docs):
        doc_id = start_id + j

        d = Document(id=doc_id)
        d.text = b'hello world'
        d.tags['id'] = doc_id
        if embedding:
            d.embedding = np.random.random([embed_dim + np.random.randint(0, jitter)])
        d.update_content_hash()

        for _ in range(chunks_per_doc):
            chunk_doc_id = next_chunk_doc_id

            c = Document(id=chunk_doc_id)
            c.text = 'i\'m chunk %d from doc %d' % (chunk_doc_id, doc_id)
            if embedding:
                c.embedding = np.random.random([embed_dim + np.random.randint(0, jitter)])
            c.tags['parent_id'] = doc_id
            c.tags['id'] = chunk_doc_id
            c.update_content_hash()
            d.chunks.append(c)
            next_chunk_doc_id += 1

        yield d


def rm_files(file_paths):
    for file_path in file_paths:
        if os.path.exists(file_path):
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path, ignore_errors=False, onerror=None)


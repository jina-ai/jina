import os
import sys
import shutil
from pathlib import Path
from typing import Iterator

import numpy as np

from jina.types.document import Document


file_dir = Path(__file__).parent
sys.path.append(str(file_dir.parent))


def random_docs(num_docs, chunks_per_doc=5, embed_dim=10, jitter=1) -> Iterator['Document']:
    c_id = 3 * num_docs  # avoid collision with docs
    for j in range(num_docs):
        with Document() as d:
            d.tags['id'] = j
            d.text = b'hello world'
            d.embedding = np.random.random([embed_dim + np.random.randint(0, jitter)])
        for k in range(chunks_per_doc):
            with Document() as c:
                c.text = 'i\'m chunk %d from doc %d' % (c_id, j)
                c.embedding = np.random.random([embed_dim + np.random.randint(0, jitter)])
                c.tags['id'] = c_id
                c.tags['parent_id'] = j
                c_id += 1
            d.chunks.append(c)
        yield d


def rm_files(file_paths):
    for file_path in file_paths:
        file_path = Path(file_path)
        if file_path.exists():
            if file_path.is_file():
                os.remove(file_path)
            elif file_path.is_dir():
                shutil.rmtree(file_path, ignore_errors=False, onerror=None)

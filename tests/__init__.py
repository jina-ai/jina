import os
import shutil
import sys
import warnings
from typing import Iterator
from os.path import dirname

import numpy as np

from jina.proto import jina_pb2
from jina.types.document import uid, Document, DocumentProto
from jina.types.ndarray.generic import NdArray


file_dir = os.path.dirname(__file__)
sys.path.append(dirname(file_dir))


def random_docs(num_docs, chunks_per_doc=5, embed_dim=10, jitter=1) -> Iterator['DocumentProto']:
    warnings.warn('since 0.7.11 the introduce of Document primitive type, this '
                  'fake-doc generator has been depreciated. Use "random_docs_new_api" instead', DeprecationWarning)
    c_id = 3 * num_docs  # avoid collision with docs
    for j in range(num_docs):
        d = jina_pb2.DocumentProto()
        d.tags['id'] = j
        d.text = b'hello world'
        NdArray(d.embedding).value = np.random.random([embed_dim + np.random.randint(0, jitter)])
        d.id = uid.new_doc_id(d)
        for k in range(chunks_per_doc):
            c = d.chunks.add()
            c.text = 'i\'m chunk %d from doc %d' % (c_id, j)
            NdArray(c.embedding).value = np.random.random([embed_dim + np.random.randint(0, jitter)])
            c.tags['id'] = c_id
            c.tags['parent_id'] = j
            c_id += 1
            c.parent_id = d.id
            c.id = uid.new_doc_id(c)
        yield d


def random_docs_new_api(num_docs, chunks_per_doc=5, embed_dim=10, jitter=1) -> Iterator['Document']:
    c_id = 3 * num_docs  # avoid collision with docs
    for j in range(num_docs):
        with Document(random_id=False) as d:
            d.tags['id'] = j
            d.text = b'hello world'
            d.embedding = np.random.random([embed_dim + np.random.randint(0, jitter)])
        for k in range(chunks_per_doc):
            with Document(random_id=False) as c:
                c.text = 'i\'m chunk %d from doc %d' % (c_id, j)
                c.embedding = np.random.random([embed_dim + np.random.randint(0, jitter)])
                c.tags['id'] = c_id
                c.tags['parent_id'] = j
                c_id += 1
            d.chunks.append(c)
        yield d


def rm_files(file_paths):
    for file_path in file_paths:
        if os.path.exists(file_path):
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path, ignore_errors=False, onerror=None)

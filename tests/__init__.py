import os
import shutil
import sys
from typing import Iterator

import numpy as np
import pytest

from jina import Document

file_dir = os.path.dirname(__file__)
sys.path.append(os.path.dirname(file_dir))


def random_docs(
    num_docs, chunks_per_doc=5, embed_dim=10, jitter=1, start_id=0, embedding=True
) -> Iterator['Document']:
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
                c.embedding = np.random.random(
                    [embed_dim + np.random.randint(0, jitter)]
                )
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


def validate_callback(mock, validate_func):
    for args, kwargs in mock.call_args_list:
        validate_func(*args, **kwargs)

    mock.assert_called()


np.random.seed(0)
d_embedding = np.array([1, 1, 1, 1, 1, 1, 1])
c_embedding = np.array([2, 2, 2, 2, 2, 2, 2])


def get_documents(chunks, same_content, nr=10, index_start=0, same_tag_content=None):
    next_chunk_id = nr + index_start
    for i in range(index_start, nr + index_start):
        with Document() as d:
            d.id = i
            if same_content:
                d.text = 'hello world'
                d.embedding = d_embedding
            else:
                d.text = f'hello world {i}'
                d.embedding = np.random.random(d_embedding.shape)
            if same_tag_content:
                d.tags['tag_field'] = 'tag data'
            elif same_tag_content is False:
                d.tags['tag_field'] = f'tag data {i}'
            for j in range(chunks):
                with Document() as c:
                    c.id = next_chunk_id
                    if same_content:
                        c.text = 'hello world from chunk'
                        c.embedding = c_embedding
                    else:
                        c.text = f'hello world from chunk {j}'
                        c.embedding = np.random.random(d_embedding.shape)
                    if same_tag_content:
                        c.tags['tag field'] = 'tag data'
                    elif same_tag_content is False:
                        c.tags['tag field'] = f'tag data {next_chunk_id}'
                next_chunk_id += 1
                d.chunks.append(c)
        yield d


def check_docs(chunk_content, chunks, same_content, docs, ids_used, index_start=0):
    for i, d in enumerate(docs):
        i += index_start
        id_int = d.id
        assert id_int not in ids_used
        ids_used.add(id_int)

        if same_content:
            assert d.text == 'hello world'
            np.testing.assert_almost_equal(d.embedding, d_embedding)
        else:
            assert d.text == f'hello world {i}'
            assert d.embedding.shape == d_embedding.shape

        assert len(d.chunks) == chunks

        for j, c in enumerate(d.chunks):
            id_int = c.id
            assert id_int not in ids_used
            ids_used.add(id_int)
            if same_content:
                if chunk_content is None:
                    chunk_content = c.content_hash
                assert c.content_hash == chunk_content
                assert c.text == 'hello world from chunk'
                np.testing.assert_almost_equal(c.embedding, c_embedding)
            else:
                assert c.text == f'hello world from chunk {j}'
                assert c.embedding.shape == c_embedding.shape


@pytest.mark.parametrize('chunks', [0, 3, 5])
@pytest.mark.parametrize('same_content', [False, True])
@pytest.mark.parametrize('nr', [0, 10, 100, 201])
def test_docs_generator(chunks, same_content, nr):
    chunk_content = None
    docs = list(get_documents(chunks=chunks, same_content=same_content, nr=nr))
    assert len(docs) == nr
    ids_used = set()
    check_docs(chunk_content, chunks, same_content, docs, ids_used)

    if nr > 0:
        index_start = 1 + len(list(ids_used))
    else:
        index_start = 1
    new_docs = list(
        get_documents(
            chunks=chunks, same_content=same_content, nr=nr, index_start=index_start
        )
    )
    new_ids = set([d.id for d in new_docs])
    assert len(new_ids.intersection(ids_used)) == 0
    check_docs(chunk_content, chunks, same_content, new_docs, ids_used, index_start)

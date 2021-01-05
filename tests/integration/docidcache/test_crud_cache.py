import os
from pathlib import Path

import numpy as np
import pytest

from jina import Flow, Document
from jina.executors.indexers import BaseIndexer
from jina.executors.indexers.keyvalue import BinaryPbIndexer
from jina.executors.indexers.vector import NumpyIndexer

cur_dir = Path(os.path.dirname(os.path.abspath(__file__)))

KV_IDX_FILENAME = 'kv_idx.bin'
VEC_IDX_FILENAME = 'vec_idx.bin'


def config(field, tmp_workspace, shards):
    os.environ['JINA_SHARDS'] = str(shards)
    os.environ['JINA_CACHE_FIELD'] = field
    os.environ['JINA_TEST_CACHE_CRUD_WORKSPACE'] = str(tmp_workspace)
    os.environ['JINA_KV_IDX_NAME'] = KV_IDX_FILENAME.split('.bin')[0]
    os.environ['JINA_VEC_IDX_NAME'] = VEC_IDX_FILENAME.split('.bin')[0]


def get_flow(indexers, shards):
    vector_pod = dict(
        uses=cur_dir / 'yml' / 'cp_cache_kv.yml',
        name='inc_vec'
    )
    pb_pod = dict(
        uses=cur_dir / 'yml' / 'cp_cache_vector.yml',
        name='inc_doc'
    )

    if shards == 3:
        sharding_config = dict(
            shards=shards,
            separated_workspace=True,
            uses_after='_merge_matches',
            polling='all',
            timeout_ready='-1'
        )
        pb_pod.update(
            sharding_config
        )
        vector_pod.update(
            sharding_config
        )

    f: Flow = (Flow()
               .add(**pb_pod)
               .add(**vector_pod))

    if indexers == 'parallel':
        vector_pod.update(
            dict(
                needs=['gateway']
            )
        )
        f = (Flow()
             .add(**pb_pod)
             .add(**vector_pod)
             .add(needs=['inc_vec', 'inc_doc']))
    return f


np.random.seed(0)
d_embedding = np.random.random([9])
c_embedding = np.random.random([9])


def get_documents(chunks, same_content, nr=10, index_start=0):
    next_chunk_id = nr + index_start
    for i in range(index_start, nr + index_start):
        with Document() as d:
            d.id = i
            if same_content:
                d.text = 'hello world'
                d.embedding = d_embedding
            else:
                d.text = f'hello world {i}'
                d.embedding = np.random.random([9])
            for j in range(chunks):
                with Document() as c:
                    c.id = next_chunk_id
                    if same_content:
                        c.text = 'hello world from chunk'
                        c.embedding = c_embedding
                    else:
                        c.text = f'hello world from chunk {j}'
                        c.embedding = np.random.random([9])

                next_chunk_id += 1
                d.chunks.append(c)
        yield d


@pytest.mark.parametrize('chunks, same_content, nr',
                         # cartesian product of possibilities
                         [(0, False, 0),
                          (0, False, 10),
                          (0, False, 100),
                          (0, True, 0),
                          (0, True, 10),
                          (0, True, 100),
                          (3, False, 0),
                          (3, False, 10),
                          (3, False, 100),
                          (3, True, 0),
                          (3, True, 10),
                          (3, True, 100),
                          (5, False, 0),
                          (5, False, 10),
                          (5, False, 100),
                          (5, True, 0),
                          (5, True, 10),
                          (5, True, 100)])
def test_docs_generator(chunks, same_content, nr):
    chunk_content = None
    docs = list(get_documents(chunks=chunks, same_content=same_content, nr=nr))
    assert len(docs) == nr
    ids_used = set()
    check_docs(chunk_content, chunks, same_content, docs, ids_used)

    if nr > 0:
        index_start = 1 + max(list(ids_used))
    else:
        index_start = 1
    new_docs = list(get_documents(chunks=chunks, same_content=same_content, nr=nr, index_start=index_start))
    new_ids = set([d.id for d in new_docs])
    assert len(new_ids.intersection(ids_used)) == 0

    check_docs(chunk_content, chunks, same_content, new_docs, ids_used, index_start)


def check_docs(chunk_content, chunks, same_content, docs, ids_used, index_start=0):
    for i, d in enumerate(docs):
        i += index_start
        id_int = int(d.id)
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
            id_int = int(c.id)
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


@pytest.mark.parametrize('indexers, field, shards, chunks, same_content',
                         [
                             # cartesian product of the parameters
                             # TODO prune these
                             ('sequential', 'id', 1, 5, False),
                             ('sequential', 'id', 3, 5, False),
                             ('sequential', 'id', 3, 5, True),
                             ('sequential', 'content_hash', 1, 0, False),
                             ('sequential', 'content_hash', 1, 0, True),
                             ('sequential', 'content_hash', 1, 5, False),
                             ('sequential', 'content_hash', 1, 5, True),
                             ('sequential', 'content_hash', 3, 5, True),
                             ('parallel', 'id', 3, 5, False),
                             ('parallel', 'id', 3, 5, True),
                             # ('parallel', 'content_hash', 1, 0, False),
                             # ('parallel', 'content_hash', 1, 0, True),
                             # ('parallel', 'content_hash', 1, 5, False),
                             # ('parallel', 'content_hash', 1, 5, True),
                             # ('parallel', 'content_hash', 3, 0, False),
                             # ('parallel', 'content_hash', 3, 0, True),
                             ('parallel', 'content_hash', 3, 5, False),
                             ('parallel', 'content_hash', 3, 5, True)
                         ])
def test_cache_crud(
        tmp_path,
        indexers,
        field,
        shards,
        chunks,
        same_content
):
    config(field, tmp_path, shards)
    f = get_flow(indexers, shards)

    docs = list(get_documents(chunks=chunks, same_content=same_content))

    # initial data index
    with f:
        f.index(docs)

    check_indexers_size(chunks, len(docs), field, tmp_path, same_content, shards, 'index')

    # new documents
    chunks_ids = np.concatenate([d.chunks for d in docs])
    index_start_new_docs = 1 + max([int(d.id) for d in np.concatenate([chunks_ids, docs])])

    new_docs = list(get_documents(chunks=chunks, same_content=same_content, index_start=index_start_new_docs))
    with f:
        f.index(new_docs)

    check_indexers_size(chunks, len(docs), field, tmp_path, same_content, shards, 'index2')

    docs.extend(new_docs)
    # delete
    with f:
        f.delete(docs)

    check_indexers_size(chunks, 0, field, tmp_path, same_content, shards, 'delete')


def check_indexers_size(chunks, nr_docs, field, tmp_path, same_content, shards, post_op):
    for indexer_fname in [KV_IDX_FILENAME, VEC_IDX_FILENAME]:
        if shards == 1:
            with BaseIndexer.load(tmp_path / indexer_fname) as indexer:
                if indexer_fname == KV_IDX_FILENAME:
                    assert isinstance(indexer, BinaryPbIndexer)
                else:
                    assert isinstance(indexer, NumpyIndexer)

                if post_op == 'delete':
                    assert indexer.size == 0
                else:
                    if field == 'content_hash' and same_content:
                        if chunks > 0:
                            assert indexer.size == 2 if post_op == 'index' else 4
                        else:
                            assert indexer.size == 1
                    else:
                        assert indexer.size == (
                                nr_docs + chunks * nr_docs) * 2 if post_op == 'index2' else nr_docs + chunks * nr_docs

        else:
            for i in range(shards):
                full_size = 0
                indexer_folder = 'docindexer' if indexer_fname == KV_IDX_FILENAME else 'vecindexer'
                with BaseIndexer.load(tmp_path / f'inc_{indexer_folder}-{i + 1}' / indexer_fname) as indexer:
                    if indexer_fname == KV_IDX_FILENAME:
                        assert isinstance(indexer, BinaryPbIndexer)
                    else:
                        assert isinstance(indexer, NumpyIndexer)
                    full_size += indexer.size

                if post_op == 'delete':
                    assert full_size == 0
                else:
                    if field == 'content_hash' and same_content:
                        if chunks > 0:
                            # one content from Doc, one from chunk
                            assert full_size == 2 if post_op == 'index' else 4
                        else:
                            assert full_size == 1
                    else:
                        assert full_size == (
                                nr_docs + chunks * nr_docs) * 2 if post_op == 'index2' else nr_docs + chunks * nr_docs

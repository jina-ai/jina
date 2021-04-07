import os
from pathlib import Path

import numpy as np
import pytest

from jina import Flow, Document
from jina.drivers.dbms import _doc_without_embedding
from jina.executors.dump import import_vectors, import_metas
from jina.executors.indexers.query import BaseQueryIndexer
from jina.executors.indexers.query.compound import QueryCompoundExecutor
from jina.logging.profile import TimeContext


def get_documents(nr=10, index_start=0, emb_size=7):
    for i in range(index_start, nr + index_start):
        with Document() as d:
            d.id = i
            d.text = f'hello world {i}'
            d.embedding = np.random.random(emb_size)
            d.tags['tag_field'] = f'tag data {i}'
        yield d


def basic_benchmark(tmpdir, docs, validate_results_nonempty, error_callback, nr_search):
    os.environ['BASIC_QUERY_WS'] = os.path.join(tmpdir, 'basic_query')
    os.environ['BASIC_INDEX_WS'] = os.path.join(tmpdir, 'basic_index')
    with Flow().add(uses='basic/query.yml') as flow:
        flow.index(docs)

    with Flow().add(uses='basic/query.yml') as flow:
        with TimeContext(
            f'### baseline - query time with {nr_search} on {len(docs)} docs'
        ):
            flow.search(
                docs[:nr_search],
                on_done=validate_results_nonempty,
                on_error=error_callback,
            )

    with Flow().add(uses='basic/index.yml') as flow_dbms:
        with TimeContext(f'### baseline - indexing: {len(docs)} docs'):
            flow_dbms.index(docs)


def assert_dump_data(dump_path, docs, shards, pea_id):
    size_shard = len(docs) // shards
    size_shard_modulus = len(docs) % shards
    ids_dump, vectors_dump = import_vectors(
        dump_path,
        str(pea_id),
    )
    if pea_id == shards - 1:
        docs_expected = docs[
            (pea_id) * size_shard : (pea_id + 1) * size_shard + size_shard_modulus
        ]
    else:
        docs_expected = docs[(pea_id) * size_shard : (pea_id + 1) * size_shard]
    print(f'### pea {pea_id} has {len(docs_expected)} docs')

    ids_dump = list(ids_dump)
    vectors_dump = list(vectors_dump)
    np.testing.assert_equal(ids_dump, [d.id for d in docs_expected])
    np.testing.assert_allclose(vectors_dump, [d.embedding for d in docs_expected])

    _, metas_dump = import_metas(
        dump_path,
        str(pea_id),
    )
    metas_dump = list(metas_dump)
    np.testing.assert_equal(
        metas_dump,
        [_doc_without_embedding(d).SerializeToString() for d in docs_expected],
    )

    # assert with Indexers
    # noinspection PyTypeChecker
    cp: QueryCompoundExecutor = BaseQueryIndexer.load_config(
        'indexer_query.yml',
        pea_id=pea_id,
        metas={'workspace': os.path.join(dump_path, 'new_ws'), 'dump_path': dump_path},
    )
    # TODO dump path needs to be passed with the initialization
    for c in cp.components:
        assert c.size == len(docs_expected)


def path_size(dump_path):
    dir_size = (
        sum(f.stat().st_size for f in Path(dump_path).glob('**/*') if f.is_file()) / 1e6
    )
    return dir_size


@pytest.mark.parametrize('shards', [6, 3, 1])
@pytest.mark.parametrize('nr_docs', [7])
@pytest.mark.parametrize('emb_size', [10])
def test_dump_keyvalue(tmpdir, shards, nr_docs, emb_size, benchmark=False):
    docs = list(get_documents(nr=nr_docs, index_start=0, emb_size=emb_size))
    assert len(docs) == nr_docs
    nr_search = 1

    os.environ['USES_AFTER'] = '_merge_matches' if shards > 1 else '_pass'
    os.environ['SHARDS'] = str(shards)

    def _validate_results_nonempty(resp):
        assert len(resp.docs) == nr_search
        for d in resp.docs:
            if nr_docs < 10:
                assert len(d.matches) == nr_docs
            else:
                # TODO does it return all of them no matter how many?
                assert len(d.matches) > 0
            for m in d.matches:
                assert m.embedding.shape[0] == emb_size
                assert _doc_without_embedding(m).SerializeToString() is not None
                assert 'hello world' in m.text
                assert f'tag data' in m.tags['tag_field']

    def error_callback(resp):
        raise Exception('error callback called')

    if benchmark:
        basic_benchmark(
            tmpdir, docs, _validate_results_nonempty, error_callback, nr_search
        )

    DUMP_PATH = os.path.join(str(tmpdir), 'dump_dir')
    os.environ['DBMS_WORKSPACE'] = os.path.join(str(tmpdir), 'index_ws')
    with Flow.load_config('flow_dbms.yml') as flow_dbms:
        with TimeContext(f'### indexing {len(docs)} docs'):
            flow_dbms.index(docs)

        with TimeContext(f'### dumping {len(docs)} docs'):
            # TODO move to control request approach
            flow_dbms.dump('indexer_dbms', DUMP_PATH, shards=shards)

        dir_size = path_size(DUMP_PATH)
        print(f'### dump path size: {dir_size} MBs')

    # assert data dumped is correct
    for pea_id in range(shards):
        assert_dump_data(DUMP_PATH, docs, shards, pea_id)


# benchmark only
@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ, reason='skip the benchmark test on github workflow'
)
def test_benchmark(tmpdir):
    # TODO 10000 seems to break the test
    nr_docs = 8000
    return test_dump_keyvalue(
        tmpdir, shards=1, nr_docs=nr_docs, emb_size=128, benchmark=True
    )

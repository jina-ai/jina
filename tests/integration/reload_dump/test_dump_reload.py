import os
import time
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pytest

from jina import Flow
from jina.drivers.dbms import doc_without_embedding
from jina.executors.dump import DumpTypes, DumpPersistor

from jina.logging.profile import TimeContext
from tests import get_documents


@contextmanager
def measure_time_context_mgr(text='Total execution time'):
    start = int(round(time.time() * 1000))
    try:
        yield
    finally:
        end_ = int(round(time.time() * 1000)) - start
        print(f'{text}: {end_ if end_ > 0 else 0} ms')


def test_dump_index(tmpdir):
    """Dumping from an Indexer"""
    docs = list(get_documents(chunks=0, same_content=False))

    os.environ['DBMS_WORKSPACE'] = str(tmpdir)
    dump_dir = os.path.join(tmpdir, 'dump')
    with Flow.load_config('flow_index.yml') as flow_index:
        flow_index.index(docs)
        # blocking operation. we cannot access both query and write handlers of the BinaryPb
        # TODO test with Mongo/PSQL which should allow async dump in a thread
        flow_index.dump(dump_dir, shards=1, formats=[DumpTypes.DEFAULT])

        flow_index.index(docs)
        # this will fail since the dump alreayd exists
        flow_index.dump(dump_dir, shards=1, formats=[DumpTypes.DEFAULT])
        flow_index.index(docs)

    assert os.path.exists(dump_dir)
    assert os.path.exists(os.path.join(dump_dir, '0', 'vectors'))

    # test data
    ids_dump, vectors_dump = DumpPersistor.import_vectors(dump_dir, '0')
    ids_dump = list(ids_dump)
    vectors_dump = list(vectors_dump)
    _, metas_dump = DumpPersistor.import_metas(dump_dir, '0')
    metas_dump = list(metas_dump)
    np.testing.assert_allclose(vectors_dump, [d.embedding for d in docs])
    np.testing.assert_equal(ids_dump, [d.id for d in docs])
    np.testing.assert_equal(
        metas_dump, [doc_without_embedding(d).SerializeToString() for d in docs]
    )


def basic_benchmark(tmpdir, docs, validate_results_nonempty, error_callback):
    os.environ['BASIC_QUERY_WS'] = os.path.join(tmpdir, 'basic_query')
    os.environ['BASIC_INDEX_WS'] = os.path.join(tmpdir, 'basic_index')
    with Flow().add(uses='basic/query.yml') as flow:
        flow.index(docs)

    with Flow().add(uses='basic/query.yml') as flow:
        flow_query_start = time.time()
        flow.search(docs, on_done=validate_results_nonempty, on_error=error_callback)
        flow_query_end = time.time()
        print(
            f'basic query time: {flow_query_end - flow_query_start} for {len(docs)} docs. docs/sec = {len(docs) / (flow_query_end - flow_query_start)}'
        )

    with Flow().add(uses='basic/index.yml') as flow_index:
        flow_index_start = time.time()
        flow_index.index(docs)
        flow_index_end = time.time()
        print(
            f'basic index time: {flow_index_end - flow_index_start} for {len(docs)} docs. docs/sec = {len(docs) / (flow_index_end - flow_index_start)}'
        )


def assert_dump_data(dump_path, docs, shards):
    # TODO test last shard
    dir_size = (
        sum(f.stat().st_size for f in Path(dump_path).glob('**/*') if f.is_file()) / 1e6
    )
    print(f'### dump path size: {dir_size} MBs')
    pea_id = 0 if shards == 1 else 1

    size_first_shard = len(docs) // shards
    ids_dump, vectors_dump = DumpPersistor.import_vectors(
        dump_path,
        str(pea_id),
    )
    ids_dump = list(ids_dump)
    vectors_dump = list(vectors_dump)
    _, metas_dump = DumpPersistor.import_metas(
        dump_path,
        str(pea_id),
    )
    metas_dump = list(metas_dump)
    np.testing.assert_allclose(
        vectors_dump, [d.embedding for d in docs[:size_first_shard]]
    )
    np.testing.assert_equal(ids_dump, [d.id for d in docs[:size_first_shard]])
    np.testing.assert_equal(
        metas_dump,
        [doc_without_embedding(d).SerializeToString() for d in docs[:size_first_shard]],
    )


@pytest.mark.parametrize('shards', [1, 3])
def test_dump_reload(tmpdir, shards):
    def validate_results_empty(resp):
        for d in resp.docs:
            assert len(d.matches) == 0

    def validate_results_nonempty(resp):
        for d in resp.docs:
            assert len(d.matches) > 0
            for m in d.matches:
                assert m.embedding is not None
                assert doc_without_embedding(m).SerializeToString() is not None

    def error_callback(resp):
        raise Exception('error callback called')

    docs = list(
        get_documents(
            chunks=0,
            same_content=False,
            nr=5000,
            index_start=0,
            same_tag_content=False,
        )
    )

    os.environ['USES_AFTER'] = '_merge_matches' if shards > 1 else '_pass'
    os.environ['SHARDS'] = str(shards)
    if shards == 1:
        # only do this once
        basic_benchmark(tmpdir, docs, validate_results_nonempty, error_callback)

    DUMP_PATH = os.path.join(str(tmpdir), 'dump_dir')
    os.environ['QUERY_WORKSPACE'] = os.path.join(str(tmpdir), 'query_ws')
    os.environ['DBMS_WORKSPACE'] = os.path.join(str(tmpdir), 'index_ws')
    with Flow.load_config('flow_query.yml') as flow_query:
        with Flow.load_config('flow_index.yml') as flow_index:
            # flow_query.search(
            #     docs[:10], on_done=validate_results_empty, on_error=error_callback
            # )
            flow_index_start = time.time()
            flow_index.index(docs)
            flow_index_end = time.time()
            print(
                f'dbms index time: {flow_index_end - flow_index_start} for {len(docs)} docs. docs/sec = {len(docs) / (flow_index_end - flow_index_start)}'
            )

            # with measure_time_context_mgr(f'### dumping {len(docs)} docs'):
            with TimeContext(f'### dumping {len(docs)} docs'):
                flow_index.dump(DUMP_PATH, shards=shards, formats=[DumpTypes.DEFAULT])

            # assert data dumped is correct
            assert_dump_data(DUMP_PATH, docs, shards)

            # with measure_time_context_mgr(f'### reloading {len(docs)} docs'):
            with TimeContext(f'### reloading {len(docs)} docs'):
                flow_query.reload(DUMP_PATH, os.path.join(tmpdir, 'new_workspace'))
            flow_query_start = time.time()
            # flow_query.search(
            #     docs[:10], on_done=validate_results_nonempty, on_error=error_callback
            # )
            flow_query_end = time.time()
            print(
                f'reload query time: {flow_query_end - flow_query_start} for {len(docs)} docs. docs/sec = {len(docs) / (flow_query_end - flow_query_start)}'
            )

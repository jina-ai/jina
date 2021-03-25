import os
import time

import numpy as np

from jina import Flow
from jina.drivers.dbms import doc_without_embedding
from jina.executors.dump import DumpTypes, DumpPersistor
from tests import get_documents


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
        # this will overwrite
        flow_index.dump(dump_dir, shards=1, formats=[DumpTypes.DEFAULT])
        flow_index.index(docs)

    assert os.path.exists(dump_dir)
    assert os.path.exists(os.path.join(dump_dir, 'vectors'))

    # test data
    ids_dump, vectors_dump = DumpPersistor.import_vectors(dump_dir)
    ids_dump = list(ids_dump)
    vectors_dump = list(vectors_dump)
    _, metas_dump = DumpPersistor.import_metas(dump_dir)
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
            f'basic query time: {flow_query_end - flow_query_start} for {len(docs)} docs. docs/sec = {len(docs)/(flow_query_end - flow_query_start)}'
        )

    with Flow().add(uses='basic/index.yml') as flow_index:
        flow_index_start = time.time()
        flow_index.index(docs)
        flow_index_end = time.time()
        print(
            f'basic index time: {flow_index_end - flow_index_start} for {len(docs)} docs. docs/sec = {len(docs)/(flow_index_end - flow_index_start)}'
        )


def test_dump_reload(tmpdir):
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
            chunks=0, same_content=False, nr=100, index_start=0, same_tag_content=False
        )
    )

    basic_benchmark(tmpdir, docs, validate_results_nonempty, error_callback)

    DUMP_PATH = os.path.join(str(tmpdir), 'dump_dir')
    os.environ['QUERY_WORKSPACE'] = os.path.join(str(tmpdir), 'query_ws')
    os.environ['DBMS_WORKSPACE'] = os.path.join(str(tmpdir), 'index_ws')
    with Flow.load_config('flow_query.yml') as flow_query:
        with Flow.load_config('flow_index.yml') as flow_index:
            flow_query.search(
                docs, on_done=validate_results_empty, on_error=error_callback
            )
            flow_index_start = time.time()
            flow_index.index(docs)
            flow_index_end = time.time()
            print(
                f'dbms index time: {flow_index_end - flow_index_start} for {len(docs)} docs. docs/sec = {len(docs)/(flow_index_end - flow_index_start)}'
            )
            flow_index.dump(DUMP_PATH, shards=1, formats=[DumpTypes.DEFAULT])

            # test data
            ids_dump, vectors_dump = DumpPersistor.import_vectors(DUMP_PATH)
            ids_dump = list(ids_dump)
            vectors_dump = list(vectors_dump)
            _, metas_dump = DumpPersistor.import_metas(DUMP_PATH)
            metas_dump = list(metas_dump)
            np.testing.assert_allclose(vectors_dump, [d.embedding for d in docs])
            np.testing.assert_equal(ids_dump, [d.id for d in docs])
            np.testing.assert_equal(
                metas_dump, [doc_without_embedding(d).SerializeToString() for d in docs]
            )

            flow_query.reload(DUMP_PATH, os.path.join(tmpdir, 'new_workspace'))
            flow_query_start = time.time()
            flow_query.search(
                docs, on_done=validate_results_nonempty, on_error=error_callback
            )
            flow_query_end = time.time()
            print(
                f'reload query time: {flow_query_end - flow_query_start} for {len(docs)} docs. docs/sec = {len(docs)/(flow_query_end - flow_query_start)}'
            )

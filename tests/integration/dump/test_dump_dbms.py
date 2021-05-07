import functools
import os
import time
from pathlib import Path
from threading import Thread
from typing import List

import numpy as np
import pytest

from jina import Flow, Document
from jina.drivers.index import DBMSIndexDriver
from jina.executors.indexers.dump import import_vectors, import_metas
from jina.executors.indexers.query import BaseQueryIndexer
from jina.executors.indexers.query.compound import CompoundQueryExecutor
from jina.logging.profile import TimeContext
from jina.peapods import Pod
from tests.distributed.helpers import get_client


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

    with Flow(return_results=True).add(uses='basic/query.yml') as flow:
        with TimeContext(
            f'### baseline - query time with {nr_search} on {len(docs)} docs'
        ):
            results = flow.search(
                docs[:nr_search],
            )
            validate_results_nonempty(results[0])

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
        [
            DBMSIndexDriver._doc_without_embedding(d).SerializeToString()
            for d in docs_expected
        ],
    )

    # assert with Indexers
    # TODO currently metas are only passed to the parent Compound, not to the inner components
    with TimeContext(f'### reloading {len(docs_expected)}'):
        # noinspection PyTypeChecker
        cp: CompoundQueryExecutor = BaseQueryIndexer.load_config(
            'indexer_query.yml',
            pea_id=pea_id,
            metas={
                'workspace': os.path.join(dump_path, 'new_ws'),
                'dump_path': dump_path,
            },
        )
    for c in cp.components:
        assert c.size == len(docs_expected)

    # test with the inner indexers separate from the Compound
    for i, indexer_file in enumerate(['basic/query_np.yml', 'basic/query_kv.yml']):
        indexer = BaseQueryIndexer.load_config(
            indexer_file,
            pea_id=pea_id,
            metas={
                'workspace': os.path.realpath(os.path.join(dump_path, f'new_ws-{i}')),
                'dump_path': dump_path,
            },
        )
        assert indexer.size == len(docs_expected)


def path_size(dump_path):
    dir_size = (
        sum(f.stat().st_size for f in Path(dump_path).glob('**/*') if f.is_file()) / 1e6
    )
    return dir_size


def _validate_results_nonempty(nr_search, nr_docs, emb_size, resp):
    assert len(resp.docs) == nr_search
    for d in resp.docs:
        if nr_docs < 10:
            # using np.testing since pytest+pycharm swallow the stack info on built-in assert
            np.testing.assert_equal(len(d.matches), nr_docs)
        else:
            np.testing.assert_(len(d.matches) > 0, 'no matches')
        for m in d.matches:
            np.testing.assert_equal(m.embedding.shape[0], emb_size)
            assert (
                DBMSIndexDriver._doc_without_embedding(m).SerializeToString()
                is not None
            )
            assert 'hello world' in m.text
            assert f'tag data' in m.tags['tag_field']


def _validate_results_empty(resp):
    assert len(resp.docs[0].matches) == 0


def _error_callback(resp):
    raise Exception('error callback called')


@pytest.mark.parametrize('shards', [5, 3, 1])
@pytest.mark.parametrize('nr_docs', [7])
@pytest.mark.parametrize('emb_size', [10])
def test_dump_dbms(
    tmpdir, mocker, shards, nr_docs, emb_size, run_basic=False, times_to_index=2
):
    """showcases using replicas + dump + rolling update with independent clients"""

    cb, docs, dump_path, nr_search = _test_dump_prepare(
        emb_size,
        nr_docs,
        run_basic,
        shards,
        tmpdir,
    )
    times_indexed = 0
    full_docs = []
    with Flow.load_config('flow_dbms.yml') as flow_dbms:
        with Flow.load_config('flow_query.yml') as flow_query:
            while times_indexed < times_to_index:
                dump_path = os.path.join(dump_path, f'dump-{str(times_indexed)}')
                client_dbms = get_client(flow_dbms.port_expose)
                client_query = get_client(flow_query.port_expose)
                docs = list(
                    get_documents(
                        nr=nr_docs,
                        index_start=times_indexed * nr_docs,
                        emb_size=emb_size,
                    )
                )
                full_docs.extend(docs)

                with TimeContext(f'### indexing {len(docs)} docs'):
                    # client is used for data requests
                    client_dbms.index(docs)

                with TimeContext(f'### dumping {len(docs)} docs'):
                    # flow object is used for ctrl requests
                    flow_dbms.dump('indexer_dbms', dump_path=dump_path, shards=shards)

                dir_size = path_size(dump_path)
                print(f'### dump path size: {dir_size} MBs')

                with TimeContext(f'### rolling update on {len(docs)}'):
                    # flow object is used for ctrl requests
                    flow_query.rolling_update('indexer_query', dump_path)

                # data request goes to client
                result = client_query.search(
                    docs[:nr_search],
                )
                cb(result[0])
                times_indexed += 1

                # assert data dumped is correct
                for pea_id in range(shards):
                    assert_dump_data(dump_path, full_docs, shards, pea_id)


def _test_dump_prepare(emb_size, nr_docs, run_basic, shards, tmpdir):
    docs = list(get_documents(nr=nr_docs, index_start=0, emb_size=emb_size))
    assert len(docs) == nr_docs
    nr_search = 3

    os.environ['USES_AFTER'] = '_merge_matches' if shards > 1 else '_pass'
    os.environ['QUERY_SHARDS'] = str(shards)

    validation_query = functools.partial(
        _validate_results_nonempty, nr_search, nr_docs * 2, emb_size
    )  # x 2 because we run it twice

    if run_basic:
        basic_benchmark(tmpdir, docs, validation_query, _error_callback, nr_search)

    dump_path = os.path.join(str(tmpdir), 'dump_dir')
    os.environ['DBMS_WORKSPACE'] = os.path.join(str(tmpdir), 'index_ws')
    os.environ['QUERY_WORKSPACE'] = os.path.join(str(tmpdir), 'query_ws')

    return validation_query, docs, dump_path, nr_search


def _assert_order_ops(ops_log, ops: List[str]):
    print(ops_log)
    assert len(ops_log) > 0
    last_idx_found = -1
    for rec in ops_log:
        for i, op in enumerate(ops):
            if op in rec:
                print(f'found {op} in {rec}')
                if i != last_idx_found + 1:
                    return False
                last_idx_found = i
    return last_idx_found == len(ops) - 1


# log of the statements in the threading example
# to assert order
operations = []


def _print_and_append_to_ops(statement):
    global operations
    operations.append(statement)
    print(statement, flush=True)


@pytest.mark.repeat(5)
@pytest.mark.parametrize('nr_docs', [700])
@pytest.mark.parametrize('emb_size', [10])
def test_threading_query_while_reloading(tmpdir, nr_docs, emb_size, mocker):
    global operations

    # TODO better way to test async procedure call order
    # patch
    def _rolling_update(self, dump_path):
        _print_and_append_to_ops(f'### calling patched rolling update')
        for i in range(len(self.replicas)):
            _print_and_append_to_ops(f'### replica {i} -- starting')
            replica = self.replicas[i]
            replica.close()
            _print_and_append_to_ops(f'### replica {i} -- went offline')
            time.sleep(3)  # wait for query to hit system when one replica is offline
            _args = self.replicas_args[i]
            _args.noblock_on_start = False
            _args.dump_path = dump_path
            new_replica = Pod(_args)
            self.enter_context(new_replica)
            _print_and_append_to_ops(f'### replica {i} - new instance online')
            self.replicas[i] = new_replica
            time.sleep(5)

    mocker.patch(
        'jina.peapods.pods.compoundpod.CompoundPod.rolling_update',
        new_callable=lambda: _rolling_update,
    )

    docs = list(get_documents(nr=nr_docs, index_start=0, emb_size=emb_size))
    assert len(docs) == nr_docs
    nr_search = 3

    dump_path = os.path.join(str(tmpdir), 'dump_dir')
    os.environ['DBMS_WORKSPACE'] = os.path.join(str(tmpdir), 'index_ws')
    os.environ['QUERY_WORKSPACE'] = os.path.join(str(tmpdir), 'query_ws')

    os.environ['USES_AFTER'] = '_pass'
    os.environ['QUERY_SHARDS'] = str(1)

    with Flow.load_config('flow_dbms.yml') as flow_dbms:
        with Flow.load_config('flow_query.yml') as flow_query:
            client_dbms = get_client(flow_dbms.port_expose)
            client_query = get_client(flow_query.port_expose)

            with TimeContext(f'### indexing {len(docs)} docs'):
                client_dbms.index(docs)

            with TimeContext(f'### dumping {len(docs)} docs'):
                flow_dbms.dump('indexer_dbms', dump_path=dump_path, shards=1)

            dir_size = path_size(dump_path)
            print(f'### dump path size: {dir_size} MBs')

            # test with query while reloading async.
            t = Thread(
                target=flow_query.rolling_update, args=('indexer_query', dump_path)
            )

            # searching on the still empty replica
            t.start()
            time.sleep(1)  # wait a bit for replica 1 to be offline
            _print_and_append_to_ops(f'### querying -- expecting empty')
            result = client_query.search(
                docs[:nr_search],
            )
            _validate_results_empty(result[0])

            t.join()

            # done with both -- we should have matches now
            cb = functools.partial(
                _validate_results_nonempty, nr_search, nr_docs, emb_size
            )

            _print_and_append_to_ops(f'### querying -- expecting data')
            result = client_query.search(
                docs[:nr_search],
            )
            cb(result[0])

    # collect logs and assert order of operations
    assert _assert_order_ops(
        operations,
        [
            '### replica 0 -- went offline',
            '### querying -- expecting empty',
            '### replica 0 - new instance online',
            '### replica 1 -- went offline',
            '### replica 1 - new instance online',
            '### querying -- expecting data',
        ],
    )
    operations = []


# benchmark only
@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ, reason='skip the benchmark test on github workflow'
)
def test_benchmark(tmpdir, mocker):
    nr_docs = 100000
    return test_dump_dbms(
        tmpdir,
        mocker,
        shards=1,
        nr_docs=nr_docs,
        emb_size=128,
        run_basic=True,
        times_to_index=1,
    )

import os
import time
from threading import Thread

from jina import Flow
from jina.excepts import BadClientCallback
from jina.executors import reload_helpers
from jina.executors.reload_helpers import DumpTypes
from tests import get_documents


def test_reload_search_async(tmpdir):
    """Show that we can reload and search at the same time using the old indexer, then switching"""
    reload_helpers.SYNC_MODE = False

    def validate_results_empty(resp):
        print(f'### {resp}')
        for d in resp.docs:
            assert len(d.matches) == 0

    def validate_results_nonempty(resp):
        print(f'### {resp}')
        for d in resp.docs:
            assert len(d.matches) > 0

    def error_callback(resp):
        print(f'## error: {resp}')

    docs = list(
        get_documents(
            chunks=0, same_content=False, nr=1, index_start=0, same_tag_content=False
        )
    )

    DUMP_PATH = "some_path"
    os.environ["HW_WORKDIR"] = str(tmpdir)
    with Flow.load_config('flow_query.yml') as flow_query:
        print(f'### first search')
        flow_query.search(docs, on_done=validate_results_empty)
        print(f'### reload')
        flow_query.reload(DUMP_PATH)
        print(f'### second search (empty)')
        flow_query.search(docs, on_done=validate_results_empty)
        time.sleep(5)
        print(f'### third search (not empty)')
        flow_query.search(docs, on_done=validate_results_nonempty)


def test_dump(tmpdir):
    from jina.drivers.dbms import DBMSIndexDriver

    """Dumping from an Indexer"""
    docs = get_documents(0, False)
    os.environ['JINA_WORKSPACE_CRUD'] = str(tmpdir)
    dump_dir = os.path.join(tmpdir, 'dump')
    with Flow.load_config('flow_index.yml') as flow_index:
        flow_index.index(docs)
        flow_index.dump(dump_dir, shards=1, formats=[DumpTypes.DEFAULT])

    assert os.path.exists(dump_dir)
    assert os.path.exists(os.path.join(dump_dir, 'vectors'))
    # TODO assert some data


def test_reload(tmpdir):
    """Show that we can achieve query while indexing, + the two tests above, in a non-blocking way"""

    # true because we want to capture it in a wrapper thread
    reload_helpers.SYNC_MODE = True

    def validate_results_empty(resp):
        print(f'### {resp}')
        for d in resp.docs:
            assert len(d.matches) == 0

    def validate_results_nonempty(resp):
        print(f'### {resp}')
        for d in resp.docs:
            assert len(d.matches) > 0

    def error_callback(resp):
        print(f'## error: {resp}')

    docs = list(
        get_documents(
            chunks=0, same_content=False, nr=1, index_start=0, same_tag_content=False
        )
    )
    new_docs = list(
        get_documents(
            chunks=0, same_content=False, nr=1, index_start=1, same_tag_content=False
        )
    )

    DUMP_PATH = os.path.join(str(tmpdir), "dump_dir")
    os.environ["HW_WORKDIR"] = os.path.join(str(tmpdir), 'query_ws')
    os.environ['JINA_WORKSPACE_CRUD'] = os.path.join(str(tmpdir), 'index_ws')
    with Flow.load_config('flow_query.yml') as flow_query:
        with Flow.load_config('flow_index.yml') as flow_index:
            flow_query.search(
                docs, on_done=validate_results_empty, on_error=error_callback
            )
            flow_index.index(new_docs)
            # we cannot dump while indexing
            flow_index.dump(DUMP_PATH, shards=1, formats=[DumpTypes.DEFAULT])
            flow_query.reload(DUMP_PATH)
            flow_query.search(
                docs, on_done=validate_results_nonempty, on_error=error_callback
            )

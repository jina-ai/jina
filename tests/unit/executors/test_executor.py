import os
from copy import deepcopy

import pytest

from jina import Executor, requests, DocumentArray, Document, DocumentArrayMemmap
from jina.executors import ReducerExecutor
from jina.executors.metas import get_default_metas


def test_executor_load_from_hub():
    exec = Executor.from_hub(
        'jinahub://DummyHubExecutor', uses_metas={'name': 'hello123'}
    )
    da = DocumentArray([Document()])
    exec.foo(da)
    assert da.texts == ['hello']
    assert exec.metas.name == 'hello123'


def test_executor_import_with_external_dependencies(capsys):
    ex = Executor.load_config('../hubble-executor/config.yml')
    assert ex.bar == 123
    ex.foo()
    out, err = capsys.readouterr()
    assert 'hello' in out


@property
def workspace(self) -> str:
    """
    Get the path of the current shard.

    :return: returns the workspace of the shard of this Executor.
    """
    return os.path.abspath(
        self.metas.workspace
        or (
            os.path.join(self.runtime_args.workspace, self.metas.name)
            if self.metas.shard_id == -1
            else os.path.join(
                self.runtime_args.workspace, self.metas.name, self.metas.shard_id
            )
        )
    )


@pytest.fixture
def replica_id(request):
    return request.param


@pytest.fixture
def shard_id(request):
    return request.param


@pytest.fixture
def test_metas_workspace_simple(tmpdir):
    metas = get_default_metas()
    metas['workspace'] = str(tmpdir)
    metas['name'] = 'test'
    return metas


@pytest.fixture
def test_bad_metas_workspace(tmpdir):
    metas = get_default_metas()
    return metas


@pytest.fixture
def test_metas_workspace_replica_peas(tmpdir, replica_id, shard_id):
    metas = get_default_metas()
    metas['workspace'] = str(tmpdir)
    metas['name'] = 'test'
    metas['replica_id'] = replica_id
    metas['shard_id'] = shard_id
    return metas


def test_executor_workspace_simple(test_metas_workspace_simple):
    executor = Executor(metas=test_metas_workspace_simple)
    assert executor.workspace == os.path.abspath(
        os.path.join(
            test_metas_workspace_simple['workspace'],
            test_metas_workspace_simple['name'],
        )
    )


def test_executor_workspace_simple_workspace(tmpdir):
    workspace = os.path.join(tmpdir, 'some_folder')
    name = 'test_meta'

    executor = Executor(metas={'name': name, 'workspace': workspace})
    assert executor.workspace == os.path.abspath(os.path.join(workspace, name))

    executor = Executor(metas={'name': name}, runtime_args={'workspace': workspace})
    assert executor.workspace == os.path.abspath(os.path.join(workspace, name))

    # metas before runtime_args
    executor = Executor(
        metas={'name': name, 'workspace': workspace},
        runtime_args={'workspace': 'test2'},
    )
    assert executor.workspace == os.path.abspath(os.path.join(workspace, name))

    executor = Executor(
        metas={'name': name, 'workspace': workspace},
        runtime_args={'shard_id': 1, 'replica_id': 2},
    )
    assert executor.workspace == os.path.abspath(
        os.path.join(workspace, name, '2', '1')
    )

    executor = Executor(
        metas={'name': name},
        runtime_args={'workspace': workspace, 'shard_id': 1, 'replica_id': 2},
    )
    assert executor.workspace == os.path.abspath(
        os.path.join(workspace, name, '2', '1')
    )


@pytest.mark.parametrize('replica_id', [0, 1, 2], indirect=True)
@pytest.mark.parametrize('shard_id', [0, 1, 2], indirect=True)
def test_executor_workspace(test_metas_workspace_replica_peas, replica_id, shard_id):
    executor = Executor(
        metas={'name': test_metas_workspace_replica_peas['name']},
        runtime_args=test_metas_workspace_replica_peas,
    )
    assert executor.workspace == os.path.abspath(
        os.path.join(
            test_metas_workspace_replica_peas['workspace'],
            test_metas_workspace_replica_peas['name'],
            str(replica_id),
            str(shard_id),
        )
    )


@pytest.mark.parametrize('replica_id', [0, 1, 2], indirect=True)
@pytest.mark.parametrize('shard_id', [None, -1], indirect=True)
def test_executor_workspace_parent_replica_nopea(
    test_metas_workspace_replica_peas, replica_id, shard_id
):
    executor = Executor(
        metas={'name': test_metas_workspace_replica_peas['name']},
        runtime_args=test_metas_workspace_replica_peas,
    )
    assert executor.workspace == os.path.abspath(
        os.path.join(
            test_metas_workspace_replica_peas['workspace'],
            test_metas_workspace_replica_peas['name'],
            str(replica_id),
        )
    )


@pytest.mark.parametrize('replica_id', [None, -1], indirect=True)
@pytest.mark.parametrize('shard_id', [0, 1, 2], indirect=True)
def test_executor_workspace_parent_noreplica_pea(
    test_metas_workspace_replica_peas, replica_id, shard_id
):
    executor = Executor(
        metas={'name': test_metas_workspace_replica_peas['name']},
        runtime_args=test_metas_workspace_replica_peas,
    )
    assert executor.workspace == os.path.abspath(
        os.path.join(
            test_metas_workspace_replica_peas['workspace'],
            test_metas_workspace_replica_peas['name'],
            str(shard_id),
        )
    )


@pytest.mark.parametrize('replica_id', [None, -1], indirect=True)
@pytest.mark.parametrize('shard_id', [None, -1], indirect=True)
def test_executor_workspace_parent_noreplica_nopea(
    test_metas_workspace_replica_peas, replica_id, shard_id
):
    executor = Executor(
        metas={'name': test_metas_workspace_replica_peas['name']},
        runtime_args=test_metas_workspace_replica_peas,
    )
    assert executor.workspace == os.path.abspath(
        os.path.join(
            test_metas_workspace_replica_peas['workspace'],
            test_metas_workspace_replica_peas['name'],
        )
    )


def test_workspace_not_exists(tmpdir):
    class MyExec(Executor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def do(self, *args, **kwargs):
            with open(os.path.join(self.workspace, 'text.txt'), 'w') as f:
                f.write('here!')

    e = MyExec(metas={'workspace': tmpdir})
    e.do()


@pytest.mark.parametrize(
    'uses_requests, expected',
    [
        (None, {'/foo', '/default', '*'}),
        ({'/nofoo': 'foo'}, {'/nofoo', '/default', '*'}),
        ({'/nofoo': 'foo', '/new': 'default'}, {'/nofoo', '/new', '*'}),
        ({'/new': 'default'}, {'/foo', '/new', '*'}),
        ({'/nofoo': 'foo', '/new': 'all'}, {'/nofoo', '/default', '/new'}),
        ({'/new': 'all'}, {'/foo', '/default', '/new'}),
    ],
)
def test_override_requests(uses_requests, expected):
    class OverrideExec(Executor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        @requests()
        def default(self, *args, **kwargs):
            pass

        @requests(on='*')
        def all(self, *args, **kwargs):
            pass

        @requests(on='/foo')
        def foo(self, *args, **kwargs):
            pass

    exec = OverrideExec(requests=uses_requests)
    assert expected == set(exec.requests.keys())


@pytest.mark.parametrize('da_cls', [DocumentArray, DocumentArrayMemmap])
def test_map_nested(da_cls):
    class NestedExecutor(Executor):
        @requests
        def foo(self, docs: DocumentArray, **kwargs):
            def bar(d: Document):
                d.text = 'hello'
                return d

            docs.apply(bar)
            return docs

    N = 2
    da = DocumentArray.empty(N)
    exec = NestedExecutor()
    da1 = exec.foo(da)
    assert da1.texts == ['hello'] * N


@pytest.mark.parametrize('n_shards', [3, 5])
@pytest.mark.parametrize('n_matches', [10, 11])
@pytest.mark.parametrize('n_chunks', [10, 11])
def test_reducer_executor(n_shards, n_matches, n_chunks):
    reducer_executor = ReducerExecutor()
    query = DocumentArray([Document() for _ in range(5)])
    docs_matrix = [deepcopy(query) for _ in range(n_shards)]
    for da in docs_matrix:
        for doc in da:
            doc.matches.extend([Document() for _ in range(n_matches)])
            doc.chunks.extend([Document() for _ in range(n_chunks)])

    reduced_da = reducer_executor.reduce(docs_matrix=docs_matrix)
    for doc in reduced_da:
        assert len(doc.matches) == n_shards * n_matches
        assert len(doc.chunks) == n_shards * n_chunks


@pytest.mark.parametrize('da_cls', [DocumentArray, DocumentArrayMemmap])
@pytest.mark.asyncio
async def test_async(da_cls):
    class AsyncExecutor(Executor):
        @requests
        async def foo(self, docs: DocumentArray, **kwargs):
            for d in docs:
                d.text = 'hello'
            return docs

    N = 2
    da = DocumentArray.empty(N)
    exec = AsyncExecutor()
    da1 = await exec.foo(docs=da)
    assert da1.texts == ['hello'] * N


def set_hello(d: Document):
    d.text = 'hello'
    return d


@pytest.mark.parametrize('da_cls', [DocumentArray, DocumentArrayMemmap])
@pytest.mark.asyncio
async def test_async_apply(da_cls):
    class AsyncExecutor(Executor):
        @requests
        async def foo(self, docs: DocumentArray, **kwargs):
            docs.apply(set_hello)
            return docs

    N = 2
    da = DocumentArray.empty(N)
    exec = AsyncExecutor()
    da1 = await exec.foo(docs=da)
    assert da1.texts == ['hello'] * N

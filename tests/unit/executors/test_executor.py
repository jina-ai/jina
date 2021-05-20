import os

import pytest

from jina import Executor
from jina.executors.metas import get_default_metas


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
            if self.metas.replica_id == -1
            else os.path.join(
                self.runtime_args.workspace, self.metas.name, self.metas.replica_id
            )
        )
    )


@pytest.fixture
def replica_id(request):
    return request.param


@pytest.fixture
def pea_id(request):
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
def test_metas_workspace_replica_peas(tmpdir, replica_id, pea_id):
    metas = get_default_metas()
    metas['workspace'] = str(tmpdir)
    metas['name'] = 'test'
    metas['replica_id'] = replica_id
    metas['pea_id'] = pea_id
    return metas


def test_executor_workspace_simple(test_metas_workspace_simple):
    executor = Executor(metas=test_metas_workspace_simple)
    assert executor.workspace == os.path.abspath(
        test_metas_workspace_simple['workspace']
    )


@pytest.mark.parametrize('replica_id', [0, 1, 2], indirect=True)
@pytest.mark.parametrize('pea_id', [0, 1, 2], indirect=True)
def test_executor_workspace(test_metas_workspace_replica_peas, replica_id, pea_id):
    executor = Executor(
        metas={'name': test_metas_workspace_replica_peas['name']},
        runtime_args=test_metas_workspace_replica_peas,
    )
    assert executor.workspace == os.path.abspath(
        os.path.join(
            test_metas_workspace_replica_peas['workspace'],
            test_metas_workspace_replica_peas['name'],
            str(replica_id),
            str(pea_id),
        )
    )


@pytest.mark.parametrize('replica_id', [0, 1, 2], indirect=True)
@pytest.mark.parametrize('pea_id', [None, -1], indirect=True)
def test_executor_workspace_parent_replica_nopea(
    test_metas_workspace_replica_peas, replica_id, pea_id
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
@pytest.mark.parametrize('pea_id', [0, 1, 2], indirect=True)
def test_executor_workspace_parent_noreplica_pea(
    test_metas_workspace_replica_peas, replica_id, pea_id
):
    executor = Executor(
        metas={'name': test_metas_workspace_replica_peas['name']},
        runtime_args=test_metas_workspace_replica_peas,
    )
    assert executor.workspace == os.path.abspath(
        os.path.join(
            test_metas_workspace_replica_peas['workspace'],
            test_metas_workspace_replica_peas['name'],
            str(pea_id),
        )
    )


@pytest.mark.parametrize('replica_id', [None, -1], indirect=True)
@pytest.mark.parametrize('pea_id', [None, -1], indirect=True)
def test_executor_workspace_parent_noreplica_nopea(
    test_metas_workspace_replica_peas, replica_id, pea_id
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

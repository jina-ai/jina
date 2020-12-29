import os

import numpy as np
import pytest

from jina.executors import BaseExecutor


@pytest.mark.parametrize('pea_id', [1, 2, 3])
def test_share_workspace(tmpdir, pea_id):
    with BaseExecutor.load_config('yaml/test-workspace.yml', separated_workspace=True, pea_id=pea_id) as executor:
        executor.touch()
        executor_dir = tmpdir.join(f'{executor.name}-{pea_id}-{executor.name}.bin')
        executor.save(executor_dir)
        assert os.path.exists(executor_dir)


@pytest.mark.parametrize('pea_id', [1, 2, 3])
def test_compound_workspace(tmpdir, pea_id):
    with BaseExecutor.load_config('yaml/test-compound-workspace.yml', separated_workspace=True,
                                  pea_id=pea_id) as executor:
        for c in executor.components:
            c.touch()
            component_dir = tmpdir.join(f'{executor.name}-{pea_id}-{c.name}.bin')
            c.save(component_dir)
            assert os.path.exists(component_dir)
        executor.touch()
        executor_dir = tmpdir.join(f'{executor.name}-{pea_id}-{executor.name}.bin')
        executor.save(executor_dir)
        assert os.path.exists(executor_dir)


@pytest.mark.parametrize('pea_id', [1, 2, 3])
def test_compound_indexer(tmpdir, pea_id):
    with BaseExecutor.load_config('yaml/test-compound-indexer.yml',
                                  separated_workspace=True, pea_id=pea_id) as e:
        for c in e:
            c.touch()
            component_dir = tmpdir.join(f'{e.name}-{pea_id}-{c.name}.bin')
            c.save(component_dir)
            assert os.path.exists(c.index_abspath)
            assert c.save_abspath.startswith(e.current_workspace)
            assert c.index_abspath.startswith(e.current_workspace)

        e.touch()
        executor_dir = tmpdir.join(f'{e.name}-{pea_id}-{e.name}.bin')
        e.save(executor_dir)
        assert os.path.exists(executor_dir)


def test_compound_indexer_rw(tmpdir):
    all_vecs = np.random.random([6, 5])
    for j in range(3):
        with BaseExecutor.load_config('yaml/test-compound-indexer2.yml', separated_workspace=True, pea_id=j) as a:
            assert a[0] == a['test_meta']
            assert not a[0].is_updated
            assert not a.is_updated
            a[0].add([j, j * 2, j * 3], [bytes(j), bytes(j * 2), bytes(j * 3)])
            a[0].add([j, j * 2, j * 3], [bytes(j), bytes(j * 2), bytes(j * 3)])
            assert a[0].is_updated
            assert a.is_updated
            assert not a[1].is_updated
            a[1].add(np.array([j * 2, j * 2 + 1]), all_vecs[(j * 2, j * 2 + 1), :])
            assert a[1].is_updated
            a.save()
            # the compound executor itself is not modified, therefore should not generate a save
            assert not os.path.exists(a.save_abspath)
            assert os.path.exists(a[0].save_abspath)
            assert os.path.exists(a[0].index_abspath)
            assert os.path.exists(a[1].save_abspath)
            assert os.path.exists(a[1].index_abspath)

    recovered_vecs = []
    for j in range(3):
        with BaseExecutor.load_config('yaml/test-compound-indexer2.yml', separated_workspace=True, pea_id=j) as a:
            recovered_vecs.append(a[1].query_handler)

    np.testing.assert_almost_equal(all_vecs, np.concatenate(recovered_vecs))

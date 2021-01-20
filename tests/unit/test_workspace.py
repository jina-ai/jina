import os

import numpy as np
import pytest

from jina.executors import BaseExecutor

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture()
def test_workspace(tmpdir):
    os.environ['JINA_TEST_WORKSPACE'] = str(tmpdir)
    os.environ['JINA_TEST_WORKSPACE_COMP1'] = os.path.join(str(tmpdir), 'component-1')
    os.environ['JINA_TEST_WORKSPACE_COMP2'] = os.path.join(str(tmpdir), 'component-2')
    yield
    del os.environ['JINA_TEST_WORKSPACE']
    del os.environ['JINA_TEST_WORKSPACE_COMP1']
    del os.environ['JINA_TEST_WORKSPACE_COMP2']


@pytest.mark.parametrize('pea_id', [-1, 0, 1, 2, 3])
def test_shard_workspace(test_workspace, pea_id):
    tmpdir = os.environ['JINA_TEST_WORKSPACE']
    with BaseExecutor.load_config(os.path.join(cur_dir, 'yaml/test-workspace.yml'), pea_id=pea_id) as executor:
        executor.index_filename = 'index_filename'
        executor.touch()
    if pea_id > 0:
        assert os.path.exists(os.path.join(tmpdir, f'{executor.name}-{executor.pea_id}', f'{executor.name}.bin'))
    else:
        assert os.path.exists(os.path.join(tmpdir, f'{executor.name}.bin'))

    with BaseExecutor.load_config(os.path.join(cur_dir, 'yaml/test-workspace.yml'), pea_id=pea_id) as executor:
        assert executor.index_filename == 'index_filename'


@pytest.mark.parametrize('pea_id', [-1, 0, 1, 2, 3])
def test_compound_indexer_no_workspace_in_components(test_workspace, pea_id):
    tmpdir = os.environ['JINA_TEST_WORKSPACE']
    with BaseExecutor.load_config(os.path.join(cur_dir, 'yaml/test-compound-indexer.yml'), pea_id=pea_id) as executor:
        assert executor.pea_id == pea_id
        assert len(executor.components) == 2
        for i, component in enumerate(executor):
            assert component.pea_id == executor.pea_id
            component.index_filename = f'index_filename-component-{i}'
            component.touch()
        executor._attached_pea = 'hey'
        executor.touch()

    if pea_id > 0:
        assert os.path.exists(os.path.join(tmpdir, f'{executor.name}-{executor.pea_id}', f'{executor.name}.bin'))
    else:
        assert os.path.exists(os.path.join(tmpdir, f'{executor.name}.bin'))

    for component in executor:
        if pea_id > 0:
            assert os.path.exists(
                os.path.join(tmpdir, f'{executor.name}-{executor.pea_id}', f'{component.name}-{component.pea_id}',
                             f'{component.name}.bin'))
        else:
            assert os.path.exists(os.path.join(tmpdir, f'{executor.name}', f'{component.name}.bin'))

    with BaseExecutor.load_config(os.path.join(cur_dir, 'yaml/test-compound-indexer.yml'), pea_id=pea_id) as executor:
        assert len(executor.components) == 2
        for i, component in enumerate(executor):
            assert component.index_filename == f'index_filename-component-{i}'
        assert executor._attached_pea == 'hey'


@pytest.mark.parametrize('pea_id', [-1, 0, 1, 2, 3])
def test_compound_indexer_with_workspace_in_components(test_workspace, pea_id):
    # the workspace in components will be ignored in compound
    tmpdir = os.environ['JINA_TEST_WORKSPACE']
    comp1_dir = os.environ['JINA_TEST_WORKSPACE_COMP1']
    comp2_dir = os.environ['JINA_TEST_WORKSPACE_COMP2']
    with BaseExecutor.load_config(os.path.join(cur_dir, 'yaml/test-compound-indexer-components-with-workspace.yml'), pea_id=pea_id) as executor:
        assert len(executor.components) == 2
        assert executor.pea_id == pea_id
        for i, component in enumerate(executor):
            assert component.pea_id == executor.pea_id
            component.index_filename = f'index_filename-component-{i}'
            component.touch()
        executor._attached_pea = 'hey'
        executor.touch()

    if pea_id > 0:
        assert os.path.exists(os.path.join(tmpdir, f'{executor.name}-{executor.pea_id}', f'{executor.name}.bin'))
    else:
        assert os.path.exists(os.path.join(tmpdir, f'{executor.name}.bin'))

    for component in executor:
        if pea_id > 0:
            assert os.path.exists(
                os.path.join(tmpdir, f'{executor.name}-{executor.pea_id}', f'{component.name}-{component.pea_id}',
                             f'{component.name}.bin'))
        else:
            assert os.path.exists(os.path.join(tmpdir, f'{executor.name}', f'{component.name}.bin'))

    with BaseExecutor.load_config(os.path.join(cur_dir, 'yaml/test-compound-indexer-components-with-workspace.yml'), pea_id=pea_id) as executor:
        assert len(executor.components) == 2
        for i, component in enumerate(executor):
            assert component.index_filename == f'index_filename-component-{i}'
        assert executor._attached_pea == 'hey'


def test_compound_indexer_rw(test_workspace):
    all_vecs = np.random.random([6, 5])
    for j in range(3):
        with BaseExecutor.load_config(os.path.join(cur_dir, 'yaml/test-compound-indexer2.yml'), pea_id=j) as a:
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

    print(f' heeey heereee')

    recovered_vecs = []
    for j in range(3):
        with BaseExecutor.load_config(os.path.join('yaml/test-compound-indexer2.yml'), pea_id=j) as a:
            print(f' a => {a[1]}')
            print(f' a => {a[1].shard_workspace}')
            print(f' a => {a[1].query_handler}')
            recovered_vecs.append(a[1].query_handler)

    np.testing.assert_almost_equal(all_vecs, np.concatenate(recovered_vecs))

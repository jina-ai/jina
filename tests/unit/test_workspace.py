import os
import shutil

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
    with BaseExecutor.load_config(
        os.path.join(cur_dir, 'yaml/test-workspace.yml'), pea_id=pea_id
    ) as executor:
        executor.index_filename = 'index_filename'
        executor.touch()
    if pea_id > 0:
        assert os.path.exists(
            os.path.join(
                tmpdir, f'{executor.name}-{executor.pea_id}', f'{executor.name}.bin'
            )
        )
    else:
        assert os.path.exists(os.path.join(tmpdir, f'{executor.name}.bin'))

    with BaseExecutor.load_config(
        os.path.join(cur_dir, 'yaml/test-workspace.yml'), pea_id=pea_id
    ) as executor:
        assert executor.index_filename == 'index_filename'


@pytest.mark.parametrize('dump_compound', [True, False])
@pytest.mark.parametrize('pea_id', [-1, 0, 1, 2, 3])
def test_compound_indexer_no_workspace_in_components(
    test_workspace, pea_id, dump_compound
):
    tmpdir = os.environ['JINA_TEST_WORKSPACE']
    with BaseExecutor.load_config(
        os.path.join(cur_dir, 'yaml/test-compound-indexer.yml'), pea_id=pea_id
    ) as executor:
        assert executor.pea_id == pea_id
        assert len(executor.components) == 2
        for i, component in enumerate(executor):
            assert component.pea_id == executor.pea_id
            component.index_filename = f'index_filename-component-{i}'
            component.touch()
        executor._attached_pea = 'hey'
        if dump_compound:
            executor.touch()

    compound_bin_expected = None
    if pea_id > 0:
        compound_bin_expected = os.path.join(
            tmpdir, f'{executor.name}-{executor.pea_id}', f'{executor.name}.bin'
        )
    else:
        compound_bin_expected = os.path.join(tmpdir, f'{executor.name}.bin')

    if dump_compound:
        assert os.path.exists(compound_bin_expected)
    else:
        assert not os.path.exists(compound_bin_expected)

    for component in executor:
        if pea_id > 0:
            assert os.path.exists(
                os.path.join(
                    tmpdir,
                    f'{executor.name}-{executor.pea_id}',
                    f'{component.name}-{component.pea_id}',
                    f'{component.name}.bin',
                )
            )
        else:
            assert os.path.exists(
                os.path.join(tmpdir, f'{executor.name}', f'{component.name}.bin')
            )

    with BaseExecutor.load_config(
        os.path.join(cur_dir, 'yaml/test-compound-indexer.yml'), pea_id=pea_id
    ) as executor:
        assert len(executor.components) == 2
        for i, component in enumerate(executor):
            assert component.index_filename == f'index_filename-component-{i}'
        if dump_compound:
            assert executor._attached_pea == 'hey'


@pytest.mark.parametrize('dump_compound', [True, False])
@pytest.mark.parametrize('pea_id', [-1, 0])
def test_compound_indexer_with_workspace_in_components(
    test_workspace, pea_id, dump_compound
):
    # the workspace in components will be ignored in compound
    tmpdir = os.environ['JINA_TEST_WORKSPACE']
    comp1_dir = os.environ['JINA_TEST_WORKSPACE_COMP1']
    comp2_dir = os.environ['JINA_TEST_WORKSPACE_COMP2']
    with BaseExecutor.load_config(
        os.path.join(
            cur_dir, 'yaml/test-compound-indexer-components-with-workspace.yml'
        ),
        pea_id=pea_id,
    ) as executor:
        assert len(executor.components) == 2
        assert executor.pea_id == pea_id
        for i, component in enumerate(executor):
            assert component.pea_id == executor.pea_id
            component.index_filename = f'index_filename-component-{i}'
            component.touch()
        executor._attached_pea = 'hey'
        if dump_compound:
            executor.touch()

    compound_bin_expected = None
    if pea_id > 0:
        compound_bin_expected = os.path.join(
            tmpdir, f'{executor.name}-{executor.pea_id}', f'{executor.name}.bin'
        )
    else:
        compound_bin_expected = os.path.join(tmpdir, f'{executor.name}.bin')

    if dump_compound:
        assert os.path.exists(compound_bin_expected)
    else:
        assert not os.path.exists(compound_bin_expected)

    for i, component in enumerate(executor):
        if pea_id > 0:
            assert os.path.exists(
                os.path.join(
                    comp1_dir if i == 0 else comp2_dir,
                    f'{component.name}-{component.pea_id}',
                    f'{component.name}.bin',
                )
            )
        else:
            assert os.path.exists(
                os.path.join(
                    comp1_dir if i == 0 else comp2_dir, f'{component.name}.bin'
                )
            )

    with BaseExecutor.load_config(
        os.path.join(
            cur_dir, 'yaml/test-compound-indexer-components-with-workspace.yml'
        ),
        pea_id=pea_id,
    ) as executor:
        assert len(executor.components) == 2
        for i, component in enumerate(executor):
            assert component.index_filename == f'index_filename-component-{i}'
        if dump_compound:
            assert executor._attached_pea == 'hey'


@pytest.mark.parametrize('pea_id', [-1, 0, 1, 2, 3])
def test_indexer_ref_indexer(test_workspace, pea_id):
    tmpdir = os.environ['JINA_TEST_WORKSPACE']
    with BaseExecutor.load_config(
        os.path.join(cur_dir, 'yaml/test-indexer-workspace.yml'), pea_id=pea_id
    ) as ref_indexer:
        ref_indexer.num_dim = 512
        ref_indexer.touch()

    if pea_id > 0:
        assert os.path.exists(
            os.path.join(
                tmpdir,
                f'{ref_indexer.name}-{ref_indexer.pea_id}',
                f'{ref_indexer.name}.bin',
            )
        )
    else:
        assert os.path.exists(os.path.join(tmpdir, f'{ref_indexer.name}.bin'))

    with BaseExecutor.load_config(
        os.path.join(cur_dir, 'yaml/test-refindexer-workspace.yml'), pea_id=pea_id
    ) as indexer:
        assert indexer.num_dim == 512


@pytest.mark.parametrize('pea_id', [-1, 0, 1, 2, 3])
def test_compound_indexer_ref_indexer(test_workspace, pea_id):
    tmpdir = os.environ['JINA_TEST_WORKSPACE']
    with BaseExecutor.load_config(
        os.path.join(cur_dir, 'yaml/test-compound-indexer2.yml'), pea_id=pea_id
    ) as compound_indexer:
        ref_indexer = compound_indexer[1]
        ref_indexer.num_dim = 512
        ref_indexer.touch()

    if pea_id > 0:
        assert os.path.exists(
            os.path.join(
                tmpdir,
                f'{compound_indexer.name}-{compound_indexer.pea_id}',
                f'{ref_indexer.name}-{ref_indexer.pea_id}',
                f'{ref_indexer.name}.bin',
            )
        )
    else:
        assert os.path.exists(
            os.path.join(tmpdir, f'{compound_indexer.name}', f'{ref_indexer.name}.bin')
        )

    with BaseExecutor.load_config(
        os.path.join(cur_dir, 'yaml/test_compount_indexer2-ref-indexer.yml'),
        pea_id=pea_id,
    ) as compound_indexer:
        indexer = compound_indexer[1]
        assert indexer.num_dim == 512


@pytest.fixture()
def test_workspace_move(tmpdir):
    os.environ['JINA_TEST_WORKSPACE'] = os.path.join(str(tmpdir), 'host')
    yield
    del os.environ['JINA_TEST_WORKSPACE']


# This test tries to simulate the situation where an executor workspace is mapped to a docker container, and therefore
# its workspace has changed.
@pytest.mark.parametrize('pea_id', [-1, 0, 1, 2, 3])
def test_simple_indexer_workspace_move_to_docker(test_workspace_move, tmpdir, pea_id):
    keys = ['0', '1']
    content = [b'a', b'b']
    old_tmpdir = os.environ['JINA_TEST_WORKSPACE']
    docker_tmpdir = os.path.join(tmpdir, 'docker')

    with BaseExecutor.load_config(
        os.path.join(cur_dir, 'yaml/test-kvindexer-workspace.yml'), pea_id=pea_id
    ) as indexer:
        indexer.add(keys, content)

    if pea_id > 0:
        assert os.path.exists(
            os.path.join(
                old_tmpdir, f'{indexer.name}-{indexer.pea_id}', f'{indexer.name}.bin'
            )
        )
    else:
        assert os.path.exists(os.path.join(old_tmpdir, f'{indexer.name}.bin'))

    shutil.copytree(os.environ['JINA_TEST_WORKSPACE'], docker_tmpdir)

    shutil.rmtree(os.environ['JINA_TEST_WORKSPACE'])

    os.environ['JINA_TEST_WORKSPACE'] = str(docker_tmpdir)

    with BaseExecutor.load_config(
        os.path.join(cur_dir, 'yaml/test-kvindexer-workspace.yml'), pea_id=pea_id
    ) as indexer:
        assert indexer.query(keys[0]) == content[0]
        assert indexer.query(keys[1]) == content[1]
        assert indexer.workspace == docker_tmpdir


def test_compound_indexer_rw(test_workspace):
    all_vecs = np.random.random([6, 5])
    for j in range(3):
        with BaseExecutor.load_config(
            os.path.join(cur_dir, 'yaml/test-compound-indexer2.yml'),
            separated_workspace=True,
            pea_id=j,
        ) as indexer:
            assert indexer[0] == indexer['test_meta']
            assert not indexer[0].is_updated
            assert not indexer.is_updated
            indexer[0].add(
                [str(j), str(j * 2), str(j * 3)], [bytes(j), bytes(j * 2), bytes(j * 3)]
            )
            assert indexer[0].is_updated
            assert indexer.is_updated
            assert not indexer[1].is_updated
            indexer[1].add([str(j), str(j * 2)], all_vecs[(j * 2, j * 2 + 1), :])
            assert indexer[1].is_updated
            indexer.save()
            # the compound executor itself is not modified, therefore should not generate a save
            assert not os.path.exists(indexer.save_abspath)
            assert os.path.exists(indexer[0].save_abspath)
            assert os.path.exists(indexer[0].index_abspath)
            assert os.path.exists(indexer[1].save_abspath)
            assert os.path.exists(indexer[1].index_abspath)

    recovered_vecs = []
    for j in range(3):
        with BaseExecutor.load_config(
            os.path.join(cur_dir, 'yaml/test-compound-indexer2.yml'),
            separated_workspace=True,
            pea_id=j,
        ) as indexer:
            recovered_vecs.append(indexer[1].query_handler)

    np.testing.assert_almost_equal(all_vecs, np.concatenate(recovered_vecs))

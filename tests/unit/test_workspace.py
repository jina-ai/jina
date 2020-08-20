import os

import numpy as np
from jina.executors import BaseExecutor
from jina.proto import jina_pb2
from tests import JinaTestCase

cur_dir = os.path.dirname(os.path.abspath(__file__))


class MyTestCase(JinaTestCase):

    def test_share_workspace(self):
        for j in range(3):
            a = BaseExecutor.load_config(os.path.join(cur_dir, 'yaml/test-workspace.yml'), True, j)
            a.touch()
            a.save()
            self.assertTrue(os.path.exists(f'{a.name}-{j}/{a.name}.bin'))
            self.add_tmpfile(f'{a.name}-{j}/{a.name}.bin')
            self.add_tmpfile(f'{a.name}-{j}')

    def test_compound_workspace(self):
        for j in range(3):
            a = BaseExecutor.load_config(os.path.join(cur_dir, 'yaml/test-compound-workspace.yml'), True, j)
            for c in a.components:
                c.touch()
                c.save()
                self.assertTrue(os.path.exists(f'{a.name}-{j}/{c.name}.bin'))
                self.add_tmpfile(f'{a.name}-{j}/{c.name}.bin')
            a.touch()
            a.save()
            self.assertTrue(os.path.exists(f'{a.name}-{j}/{a.name}.bin'))
            self.add_tmpfile(f'{a.name}-{j}/{a.name}.bin')
            self.add_tmpfile(f'{a.name}-{j}')

    def test_compound_indexer(self):
        all_subspace = set()
        for j in range(3):
            a = BaseExecutor.load_config(os.path.join(cur_dir, 'yaml/test-compound-indexer.yml'), True, j)
            for c in a:
                c.touch()
                print(c.save_abspath)
                print(c.index_abspath)
                c.save()
                self.assertTrue(os.path.exists(c.save_abspath))
                self.assertTrue(os.path.exists(c.index_abspath))
                self.add_tmpfile(c.save_abspath, c.index_abspath)

                self.assertTrue(c.save_abspath.startswith(a.current_workspace))
                self.assertTrue(c.index_abspath.startswith(a.current_workspace))
            a.touch()
            a.save()
            self.assertTrue(os.path.exists(a.save_abspath))
            self.add_tmpfile(a.save_abspath)
            self.add_tmpfile(a.current_workspace)
            all_subspace.add(a.current_workspace)

        assert len(all_subspace) == 3

    def test_compound_indexer_rw(self):
        all_vecs = np.random.random([6, 5])
        for j in range(3):
            a = BaseExecutor.load_config(os.path.join(cur_dir, 'yaml/test-compound-indexer2.yml'), True, j)
            assert a[0] == a['test_meta']
            self.assertFalse(a[0].is_updated)
            self.assertFalse(a.is_updated)
            a[0].add([jina_pb2.Document()])
            self.assertTrue(a[0].is_updated)
            self.assertTrue(a.is_updated)
            self.assertFalse(a[1].is_updated)
            a[1].add(np.array([j * 2, j * 2 + 1]), all_vecs[(j * 2, j * 2 + 1), :])
            self.assertTrue(a[1].is_updated)
            a.save()
            # the compound executor itself is not modified, therefore should not generate a save
            self.assertFalse(os.path.exists(a.save_abspath))
            self.assertTrue(os.path.exists(a[0].save_abspath))
            self.assertTrue(os.path.exists(a[0].index_abspath))
            self.assertTrue(os.path.exists(a[1].save_abspath))
            self.assertTrue(os.path.exists(a[1].index_abspath))
            self.add_tmpfile(a[0].save_abspath, a[1].save_abspath, a[0].index_abspath, a[1].index_abspath,
                             a.current_workspace)

        recovered_vecs = []
        for j in range(3):
            a = BaseExecutor.load_config(os.path.join(cur_dir, 'yaml/test-compound-indexer2.yml'), True, j)
            recovered_vecs.append(a[1].query_handler)

        np.testing.assert_almost_equal(all_vecs, np.concatenate(recovered_vecs))

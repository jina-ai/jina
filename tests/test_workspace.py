import os

import numpy as np
from jina.executors import BaseExecutor
from tests import JinaTestCase


class MyTestCase(JinaTestCase):

    def test_share_workspace(self):
        for j in range(3):
            a = BaseExecutor.load_config('yaml/test-workspace.yml', True, j)
            a.touch()
            a.save()
            self.assertTrue(os.path.exists('%s-%s/%s.bin' % (a.name, j, a.name)))
            self.add_tmpfile('%s-%s/%s.bin' % (a.name, j, a.name))
            self.add_tmpfile('%s-%s' % (a.name, j))

    def test_compound_workspace(self):
        for j in range(3):
            a = BaseExecutor.load_config('yaml/test-compound-workspace.yml', True, j)
            for c in a.components:
                c.touch()
                c.save()
                self.assertTrue(os.path.exists('%s-%s/%s.bin' % (a.name, j, c.name)))
                self.add_tmpfile('%s-%s/%s.bin' % (a.name, j, c.name))
            a.touch()
            a.save()
            self.assertTrue(os.path.exists('%s-%s/%s.bin' % (a.name, j, a.name)))
            self.add_tmpfile('%s-%s/%s.bin' % (a.name, j, a.name))
            self.add_tmpfile('%s-%s' % (a.name, j))

    def test_compound_indexer(self):
        all_subspace = set()
        for j in range(3):
            a = BaseExecutor.load_config('yaml/test-compound-indexer.yml', True, j)
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

        self.assertEqual(len(all_subspace), 3)

    def test_compound_indexer_rw(self):
        all_vecs = np.random.random([6, 5])
        for j in range(3):
            a = BaseExecutor.load_config('yaml/test-compound-indexer2.yml', True, j)
            self.assertEqual(a[0], a['test_meta'])
            self.assertFalse(a[0].is_updated)
            self.assertFalse(a.is_updated)
            a[0].add(j)
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

        for j in range(3):
            a = BaseExecutor.load_config('yaml/test-compound-indexer2.yml', True, j)
            print(a)

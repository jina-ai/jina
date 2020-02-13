import os
import unittest


class JinaTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp_files = []
        os.environ['TEST_WORKDIR'] = os.getcwd()

    def tearDown(self) -> None:
        for k in self.tmp_files:
            if os.path.exists(k):
                os.remove(k)

    def add_tmpfile(self, path):
        self.tmp_files.append(path)

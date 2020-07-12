import os
import shutil
import sys
import unittest
from os.path import dirname


class JinaTestCase(unittest.TestCase):
    timeout = 30

    def setUp(self) -> None:
        self.tmp_files = []
        os.environ['TEST_WORKDIR'] = os.getcwd()

    def tearDown(self) -> None:
        for k in self.tmp_files:
            if os.path.exists(k):
                if os.path.isfile(k):
                    os.remove(k)
                elif os.path.isdir(k):
                    shutil.rmtree(k, ignore_errors=False, onerror=None)

    def add_tmpfile(self, *path):
        self.tmp_files.extend(path)


file_dir = os.path.dirname(__file__)
sys.path.append(dirname(file_dir))

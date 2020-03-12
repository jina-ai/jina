import os
import shutil
import unittest


class JinaTestCase(unittest.TestCase):

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


dirname = os.path.dirname(__file__)


def getpath(p):
    return os.path.join(dirname, p)

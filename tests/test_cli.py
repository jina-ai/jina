import subprocess
import unittest

from tests import JinaTestCase


class MyTestCase(JinaTestCase):

    def test_cli(self):
        for j in ('pod', 'pea', 'gateway', 'log', 'check', 'ping', 'client', 'flow'):
            subprocess.check_call(['jina', j, '--help'])


if __name__ == '__main__':
    unittest.main()

import subprocess
import unittest

from tests import JinaTestCase


class MyTestCase(JinaTestCase):

    def test_cli(self):
        for j in ('pod', 'pea', 'gateway', 'log',
                  'check', 'ping', 'client', 'flow', 'hello-world'):
            subprocess.check_call(['jina', j, '--help'])

    def test_helloworld(self):
        subprocess.check_call(['jina', 'hello-world'])


if __name__ == '__main__':
    unittest.main()

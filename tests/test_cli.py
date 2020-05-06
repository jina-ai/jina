import os
import subprocess
import unittest

from pkg_resources import resource_filename

from jina.flow import Flow
from jina.main.parser import set_hw_parser
from tests import JinaTestCase


class MyTestCase(JinaTestCase):

    def test_cli(self):
        for j in ('pod', 'pea', 'gateway', 'log',
                  'check', 'ping', 'client', 'flow', 'hello-world', 'export-api'):
            subprocess.check_call(['jina', j, '--help'])
        subprocess.check_call(['jina'])

    def test_helloworld(self):
        subprocess.check_call(['jina', 'hello-world'])

    def test_helloworld_py(self):
        from jina.main.parser import set_hw_parser
        from jina.helloworld import hello_world
        hello_world(set_hw_parser().parse_args([]))

    def test_helloworld_flow(self):
        args = set_hw_parser().parse_args([])

        os.environ['RESOURCE_DIR'] = resource_filename('jina', 'resources')
        os.environ['SHARDS'] = str(args.shards)
        os.environ['REPLICAS'] = str(args.replicas)
        os.environ['HW_WORKDIR'] = args.workdir
        os.environ['WITH_LOGSERVER'] = str(args.logserver)

        a = Flow.load_config(resource_filename('jina', '/'.join(('resources', 'helloworld.flow.index.yml'))))
        a.build()
        for p in a._pod_nodes.values():
            print(f'{p.name}, {p.needs}')


if __name__ == '__main__':
    unittest.main()

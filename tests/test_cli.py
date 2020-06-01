import os
import subprocess
import unittest
from pathlib import Path

from jina.clients import py_client
from jina.clients.python.io import input_numpy
from jina.flow import Flow
from jina.helloworld import download_data
from jina.main.parser import set_hw_parser
from pkg_resources import resource_filename
from tests import JinaTestCase


class MyTestCase(JinaTestCase):

    def test_cli(self):
        for j in ('pod', 'pea', 'gateway', 'log',
                  'check', 'ping', 'client', 'flow', 'hello-world', 'export-api'):
            subprocess.check_call(['jina', j, '--help'])
        subprocess.check_call(['jina'])

    def test_helloworld(self):
        subprocess.check_call(['jina', 'hello-world'])

    @unittest.skipIf('GITHUB_WORKFLOW' in os.environ, 'skip the network test on github workflow')
    def test_helloworld_py(self):
        from jina.main.parser import set_hw_parser
        from jina.helloworld import hello_world
        hello_world(set_hw_parser().parse_args([]))

    @unittest.skipIf('GITHUB_WORKFLOW' in os.environ, 'skip the network test on github workflow')
    def test_helloworld_flow(self):
        args = set_hw_parser().parse_args([])

        os.environ['RESOURCE_DIR'] = resource_filename('jina', 'resources')
        os.environ['SHARDS'] = str(args.shards)
        os.environ['REPLICAS'] = str(args.replicas)
        os.environ['HW_WORKDIR'] = args.workdir
        os.environ['WITH_LOGSERVER'] = str(args.logserver)

        f = Flow.load_config(resource_filename('jina', '/'.join(('resources', 'helloworld.flow.index.yml'))))

        targets = {
            'index': {
                'url': args.index_data_url,
                'filename': os.path.join(args.workdir, 'index-original')
            },
            'query': {
                'url': args.query_data_url,
                'filename': os.path.join(args.workdir, 'query-original')
            }
        }

        # download the data
        Path(args.workdir).mkdir(parents=True, exist_ok=True)
        download_data(targets)

        # run it!
        with f:
            py_client(host=f.host,
                      port_grpc=f.port_grpc,
                      ).index(input_numpy(targets['index']['data']), batch_size=args.index_batch_size)


if __name__ == '__main__':
    unittest.main()

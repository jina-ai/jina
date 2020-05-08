import os
import subprocess
import unittest
from pathlib import Path

from pkg_resources import resource_filename

from jina.clients import py_client
from jina.flow import Flow
from jina.helloworld import download_data, input_fn
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
                      batch_size=args.index_batch_size).index(input_fn(targets['index']['filename']))


if __name__ == '__main__':
    unittest.main()

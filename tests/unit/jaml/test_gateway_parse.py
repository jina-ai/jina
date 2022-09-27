import os

import yaml

from jina.jaml import JAML
from jina.serve.executors import BaseExecutor
from jina.serve.gateway import BaseGateway


class MyDummyGateway(BaseGateway):
    async def setup_server(self):
        self.server = 'dummy server'

    async def run_server(self):
        self.logger.info(self.server)

    async def teardown(self):
        pass

    async def stop_server(self):
        self.server = None


def test_cls_from_tag():
    assert JAML.cls_from_tag('MyDummyGateway') == MyDummyGateway
    assert JAML.cls_from_tag('!MyDummyGateway') == MyDummyGateway
    assert JAML.cls_from_tag('BaseGateway') == BaseGateway
    assert JAML.cls_from_tag('Nonexisting') is None


def test_base_jtype(tmpdir):
    gateway_path = os.path.join(tmpdir, 'gateway.yml')

    g = BaseGateway()
    g.save_config(gateway_path)
    with open(gateway_path, 'r') as file:
        conf = yaml.safe_load(file)
        assert 'jtype' in conf
        assert conf['jtype'] == 'BaseGateway'

    assert type(BaseGateway.load_config(gateway_path)) == BaseGateway


def test_custom_jtype(tmpdir):
    gateway_path = os.path.join(tmpdir, 'gateway.yml')

    e = MyDummyGateway()
    e.save_config(gateway_path)
    with open(gateway_path, 'r') as file:
        conf = yaml.safe_load(file)
        assert 'jtype' in conf
        assert conf['jtype'] == 'MyDummyGateway'

    assert type(BaseGateway.load_config(gateway_path)) == MyDummyGateway

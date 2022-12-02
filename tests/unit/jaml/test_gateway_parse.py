import os

import pytest
import yaml

from jina import Gateway
from jina.jaml import JAML
from jina.serve.executors import BaseExecutor


class MyDummyGateway(Gateway):
    async def setup_server(self):
        self.server = 'dummy server'

    async def run_server(self):
        self.logger.info(self.server)

    async def shutdown(self):
        pass


def test_cls_from_tag():
    assert JAML.cls_from_tag('MyDummyGateway') == MyDummyGateway
    assert JAML.cls_from_tag('!MyDummyGateway') == MyDummyGateway
    assert JAML.cls_from_tag('BaseGateway') == Gateway
    assert JAML.cls_from_tag('Nonexisting') is None


def test_base_jtype(tmpdir):
    gateway_path = os.path.join(tmpdir, 'gateway.yml')
    from jina.serve.runtimes.gateway import BaseGateway

    g = BaseGateway.load_config('BaseGateway', runtime_args={'port': [12345]})
    g.save_config(gateway_path)
    with open(gateway_path, 'r') as file:
        conf = yaml.safe_load(file)
        assert 'jtype' in conf
        assert conf['jtype'] == 'BaseGateway'

    assert (
        type(Gateway.load_config(gateway_path, runtime_args={'port': [12345]}))
        == Gateway
    )


def test_custom_jtype(tmpdir):
    gateway_path = os.path.join(tmpdir, 'gateway.yml')

    e = Gateway.load_config('MyDummyGateway', runtime_args={'port': [12345]})
    e.save_config(gateway_path)
    with open(gateway_path, 'r') as file:
        conf = yaml.safe_load(file)
        assert 'jtype' in conf
        assert conf['jtype'] == 'MyDummyGateway'

    assert (
        type(Gateway.load_config(gateway_path, runtime_args={'port': [12345]}))
        == MyDummyGateway
    )

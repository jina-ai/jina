import os

import yaml

from jina.serve.runtimes.gateway.gateway import BaseGateway, Gateway
from jina.jaml import JAML


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
    assert JAML.cls_from_tag('BaseGateway') == BaseGateway
    assert JAML.cls_from_tag('Nonexisting') is None


def test_base_jtype(tmpdir):
    gateway_path = os.path.join(tmpdir, 'gateway.yml')

    g = BaseGateway.load_config('Gateway', runtime_args={'port': [12345]})
    g.save_config(gateway_path)
    with open(gateway_path, 'r', encoding='utf-8') as file:
        conf = yaml.safe_load(file)
        assert 'jtype' in conf
        assert conf['jtype'] == 'Gateway'

    assert (
        type(BaseGateway.load_config(gateway_path, runtime_args={'port': [12345]}))
        == Gateway
    )


def test_custom_jtype(tmpdir):
    gateway_path = os.path.join(tmpdir, 'gateway.yml')

    e = BaseGateway.load_config('MyDummyGateway', runtime_args={'port': [12345]})
    print(f' e {type(e)} => {e.__dict__}')
    e.save_config(gateway_path)
    with open(gateway_path, 'r', encoding='utf-8') as file:
        conf = yaml.safe_load(file)
        assert 'jtype' in conf
        assert conf['jtype'] == 'MyDummyGateway'

    assert (
        type(BaseGateway.load_config(gateway_path, runtime_args={'port': [12345]}))
        == MyDummyGateway
    )

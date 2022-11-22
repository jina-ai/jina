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


@pytest.fixture
def dummy_gateway_runtime_args():
    return {
        'name': None,
        'port': None,
        'protocol': None,
        'tracing': None,
        'tracer_provider': None,
        'grpc_tracing_server_interceptors': None,
        'graph_description': '{}',
        'graph_conditions': '{}',
        'deployments_addresses': '{}',
        'deployments_metadata': '{}',
        'deployments_no_reduce': '{}',
        'timeout_send': -1,
        'retries': 2,
        'compression': None,
        'runtime_name': 'test',
        'prefetch': None,
        'metrics_registry': None,
        'meter': None,
        'aio_tracing_client_interceptors': None,
        'tracing_client_interceptor': None,
    }


def test_cls_from_tag():
    assert JAML.cls_from_tag('MyDummyGateway') == MyDummyGateway
    assert JAML.cls_from_tag('!MyDummyGateway') == MyDummyGateway
    assert JAML.cls_from_tag('BaseGateway') == Gateway
    assert JAML.cls_from_tag('Nonexisting') is None


def test_base_jtype(tmpdir, dummy_gateway_runtime_args):
    gateway_path = os.path.join(tmpdir, 'gateway.yml')

    g = Gateway.load_config('BaseGateway', runtime_args=dummy_gateway_runtime_args)
    g.save_config(gateway_path)
    with open(gateway_path, 'r') as file:
        conf = yaml.safe_load(file)
        assert 'jtype' in conf
        assert conf['jtype'] == 'BaseGateway'

    assert (
        type(Gateway.load_config(gateway_path, runtime_args=dummy_gateway_runtime_args))
        == Gateway
    )


def test_custom_jtype(tmpdir, dummy_gateway_runtime_args):
    gateway_path = os.path.join(tmpdir, 'gateway.yml')

    e = Gateway.load_config('MyDummyGateway', runtime_args=dummy_gateway_runtime_args)
    e.save_config(gateway_path)
    with open(gateway_path, 'r') as file:
        conf = yaml.safe_load(file)
        assert 'jtype' in conf
        assert conf['jtype'] == 'MyDummyGateway'

    assert (
        type(Gateway.load_config(gateway_path, runtime_args=dummy_gateway_runtime_args))
        == MyDummyGateway
    )

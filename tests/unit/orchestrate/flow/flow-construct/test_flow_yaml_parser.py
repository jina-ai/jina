import os
from pathlib import Path

import numpy as np
import pytest
from docarray.document.generators import from_ndarray

from jina import Executor, Flow
from jina.enums import GatewayProtocolType
from jina.excepts import BadYAMLVersion
from jina.jaml import JAML
from jina.jaml.parsers import get_supported_versions
from jina.parsers.flow import set_flow_parser

cur_dir = Path(__file__).parent


def test_load_flow_from_empty_yaml():
    with open(cur_dir / 'yaml' / 'dummy-flow.yml') as fp:
        JAML.load(fp)

    with open(cur_dir / 'yaml' / 'dummy-flow.yml') as fp:
        Flow.load_config(fp)


def test_support_versions():
    assert get_supported_versions(Flow) == ['1']


def test_load_legacy_and_v1():
    Flow.load_config('yaml/flow-legacy-syntax.yml')
    Flow.load_config('yaml/flow-v1-syntax.yml')

    # this should fallback to v1
    Flow.load_config('yaml/flow-v1.0-syntax.yml')

    with pytest.raises(BadYAMLVersion):
        Flow.load_config('yaml/flow-v99-syntax.yml')


@pytest.mark.slow
def test_add_needs_inspect(tmpdir):
    f1 = (
        Flow()
        .add(name='executor0', needs='gateway')
        .add(name='executor1', needs='gateway')
        .inspect()
        .needs(['executor0', 'executor1'])
    )
    with f1:
        _ = f1.index(from_ndarray(np.random.random([5, 5])))
        f2 = Flow.load_config('yaml/flow-v1.0-syntax.yml')

        with f2:
            _ = f2.index(from_ndarray(np.random.random([5, 5])))

            assert f1 == f2


def test_load_dump_load(tmpdir):
    """TODO: Dumping valid yaml is out of scope of PR#1442, to do in separate PR"""
    f1 = Flow.load_config('yaml/flow-legacy-syntax.yml')
    f1.save_config(str(Path(tmpdir) / 'a0.yml'))
    f2 = Flow.load_config('yaml/flow-v1.0-syntax.yml')
    f2.save_config(str(Path(tmpdir) / 'a1.yml'))


def test_load_modify_dump_load(tmpdir):
    f: Flow = Flow.load_config('yaml/flow-gateway.yml')
    # assert vars inside `with`
    assert f._kwargs['name'] == 'abc'
    assert f.port == 12345
    assert f.protocol == GatewayProtocolType.HTTP
    # assert executor args
    assert f._deployment_nodes['custom1'].args.uses == 'jinahub://CustomExecutor1'
    assert f._deployment_nodes['custom2'].args.uses == 'CustomExecutor2'
    assert int(f._deployment_nodes['custom2'].args.port) == 23456

    # change args inside `with`
    f.port = 12346
    f.protocol = GatewayProtocolType.WEBSOCKET
    # change executor args
    f._deployment_nodes['custom2'].args.port = 23457

    f.save_config(str(Path(tmpdir) / 'a0.yml'))
    f1: Flow = Flow.load_config(str(Path(tmpdir) / 'a0.yml'))

    # assert args from original yaml
    assert f1._kwargs['name'] == 'abc'
    assert 'custom1' in f1._deployment_nodes
    assert 'custom2' in f1._deployment_nodes
    assert f1._deployment_nodes['custom1'].args.uses == 'jinahub://CustomExecutor1'
    assert f1._deployment_nodes['custom2'].args.uses == 'CustomExecutor2'
    # assert args modified in code
    assert f1.port == 12346
    assert f1.protocol == GatewayProtocolType.WEBSOCKET
    assert int(f1._deployment_nodes['custom2'].args.port) == 23457


def test_dump_load_build(monkeypatch):
    f: Flow = Flow.load_config(
        '''
    jtype: Flow
    with:
        name: abc
        port: 12345
        protocol: http
    executors:
        - name: executor1
          port: 45678
          shards: 2
        - name: executor2
          uses: docker://exec
          host: 1.2.3.4
        - name: executor3
          uses: docker://exec
          shards: 2
    '''
    ).build()

    f1: Flow = Flow.load_config(JAML.dump(f)).build()
    # these were passed by the user
    assert f.port == f1.port
    assert f.protocol == f1.protocol
    assert int(f['executor1'].args.port) == int(f1['executor1'].args.port)
    assert f['executor2'].args.host == f1['executor2'].args.host
    # this was set during `load_config`
    assert int(f['executor2'].args.port) == int(f1['executor2'].args.port)

    monkeypatch.setenv('JINA_FULL_CLI', 'true')
    f2: Flow = Flow.load_config(JAML.dump(f)).build()
    # these were passed by the user
    assert int(f.port) == int(f2.port)
    # validate gateway args (set during build)
    assert int(f['gateway'].args.port) == int(f2['gateway'].args.port)


def test_load_flow_with_port():
    f = Flow.load_config('yaml/test-flow-port.yml')
    with f:
        assert int(f.port) == 12345


def test_load_flow_from_cli():
    a = set_flow_parser().parse_args(['--uses', 'yaml/test-flow-port.yml'])
    f = Flow.load_config(a.uses)
    with f:
        assert int(f.port) == 12345


def test_load_flow_from_yaml():
    with open(cur_dir.parent.parent.parent / 'yaml' / 'test-flow.yml') as fp:
        _ = Flow.load_config(fp)


def test_flow_yaml_dump(tmpdir):
    f = Flow()
    f.save_config(os.path.join(str(tmpdir), 'test1.yml'))
    fl = Flow.load_config(os.path.join(str(tmpdir), 'test1.yml'))
    assert f.args.inspect == fl.args.inspect


def test_flow_yaml_from_string():
    f1 = Flow.load_config('yaml/flow-v1.0-syntax.yml')
    with open(str(cur_dir / 'yaml' / 'flow-v1.0-syntax.yml')) as fp:
        str_yaml = fp.read()
        assert isinstance(str_yaml, str)
        f2 = Flow.load_config(str_yaml)
        assert f1 == f2

    f3 = Flow.load_config(
        '!Flow\nversion: 1.0\ndeployments: [{name: ppp0, uses: _merge}, name: aaa1]'
    )
    assert 'ppp0' in f3._deployment_nodes.keys()
    assert 'aaa1' in f3._deployment_nodes.keys()
    assert f3.num_deployments == 2


class DummyEncoder(Executor):
    pass


def test_flow_uses_from_dict():
    d1 = {'jtype': 'DummyEncoder', 'metas': {'name': 'dummy1'}}
    with Flow().add(uses=d1):
        pass


def test_flow_yaml_override_with_protocol():
    from jina.enums import GatewayProtocolType

    path = os.path.join(
        cur_dir.parent.parent.parent, 'yaml/examples/faiss/flow-index.yml'
    )
    f1 = Flow.load_config(path)
    assert f1.protocol == GatewayProtocolType.GRPC
    f2 = Flow.load_config(path, uses_with={'protocol': 'http'})
    assert f2.protocol == GatewayProtocolType.HTTP
    f3 = Flow.load_config(path, uses_with={'protocol': 'websocket'})
    assert f3.protocol == GatewayProtocolType.WEBSOCKET


def test_load_flow_with_gateway():
    path = os.path.join(cur_dir.parent.parent.parent, 'yaml/flow_with_gateway.yml')
    flow = Flow.load_config(
        path,
        uses_with={'protocol': 'grpc', 'port': 12345},
    )
    with flow:
        # protocol and port are overridden by the gateway configuration
        assert flow.protocol == GatewayProtocolType.HTTP
        assert flow.port == 12344

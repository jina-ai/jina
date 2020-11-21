import os

import pytest
import requests
import numpy as np

from jina import JINA_GLOBAL
from jina.checker import NetworkChecker
from jina.enums import FlowOptimizeLevel, SocketType
from jina.flow import Flow
from jina.parser import set_pea_parser, set_ping_parser, set_flow_parser, set_pod_parser
from jina.peapods.pea import BasePea
from jina.peapods.pod import BasePod
from jina.proto.jina_pb2 import DocumentProto
from jina.types.request.common import IndexDryRunRequest
from tests import random_docs, rm_files

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_ping():
    a1 = set_pea_parser().parse_args([])
    a2 = set_ping_parser().parse_args(['0.0.0.0', str(a1.port_ctrl), '--print-response'])
    a3 = set_ping_parser().parse_args(['0.0.0.1', str(a1.port_ctrl), '--timeout', '1000'])

    with pytest.raises(SystemExit) as cm:
        with BasePea(a1):
            NetworkChecker(a2)

    assert cm.value.code == 0

    # test with bad addresss
    with pytest.raises(SystemExit) as cm:
        with BasePea(a1):
            NetworkChecker(a3)

    assert cm.value.code == 1


def test_flow_with_jump():
    f = (Flow().add(name='r1')
         .add(name='r2')
         .add(name='r3', needs='r1')
         .add(name='r4', needs='r2')
         .add(name='r5', needs='r3')
         .add(name='r6', needs='r4')
         .add(name='r8', needs='r6')
         .add(name='r9', needs='r5')
         .add(name='r10', needs=['r9', 'r8']))

    with f:
        f.dry_run()

    node = f._pod_nodes['gateway']
    assert node.head_args.socket_in == SocketType.PULL_CONNECT
    assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

    node = f._pod_nodes['r1']
    assert node.head_args.socket_in == SocketType.PULL_BIND
    assert node.tail_args.socket_out == SocketType.PUB_BIND

    node = f._pod_nodes['r2']
    assert node.head_args.socket_in == SocketType.SUB_CONNECT
    assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

    node = f._pod_nodes['r3']
    assert node.head_args.socket_in == SocketType.SUB_CONNECT
    assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

    node = f._pod_nodes['r4']
    assert node.head_args.socket_in == SocketType.PULL_BIND
    assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

    node = f._pod_nodes['r5']
    assert node.head_args.socket_in == SocketType.PULL_BIND
    assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

    node = f._pod_nodes['r6']
    assert node.head_args.socket_in == SocketType.PULL_BIND
    assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

    node = f._pod_nodes['r8']
    assert node.head_args.socket_in == SocketType.PULL_BIND
    assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

    node = f._pod_nodes['r9']
    assert node.head_args.socket_in == SocketType.PULL_BIND
    assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

    node = f._pod_nodes['r10']
    assert node.head_args.socket_in == SocketType.PULL_BIND
    assert node.tail_args.socket_out == SocketType.PUSH_BIND

    for name, node in f._pod_nodes.items():
        assert node.peas_args['peas'][0] == node.head_args
        assert node.peas_args['peas'][0] == node.tail_args

    f.save_config('tmp.yml')
    Flow.load_config('tmp.yml')

    with Flow.load_config('tmp.yml') as fl:
        fl.dry_run()

    rm_files(['tmp.yml'])


def test_simple_flow():
    bytes_gen = (b'aaa' for _ in range(10))

    def bytes_fn():
        for _ in range(100):
            yield b'aaa'

    f = (Flow()
         .add())

    with f:
        f.index(input_fn=bytes_gen)

    with f:
        f.index(input_fn=bytes_fn)

    with f:
        f.index(input_fn=bytes_fn)
        f.index(input_fn=bytes_fn)

    node = f._pod_nodes['gateway']
    assert node.head_args.socket_in == SocketType.PULL_CONNECT
    assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

    node = f._pod_nodes['pod0']
    assert node.head_args.socket_in == SocketType.PULL_BIND
    assert node.tail_args.socket_out == SocketType.PUSH_BIND

    for name, node in f._pod_nodes.items():
        assert node.peas_args['peas'][0] == node.head_args
        assert node.peas_args['peas'][0] == node.tail_args


def test_load_flow_from_yaml():
    with open(os.path.join(cur_dir, '../yaml/test-flow.yml')) as fp:
        a = Flow.load_config(fp)
        with open(os.path.join(cur_dir, '../yaml/swarm-out.yml'), 'w') as fp, a:
            a.to_swarm_yaml(fp)
        rm_files([os.path.join(cur_dir, '../yaml/swarm-out.yml')])


def test_flow_identical():
    with open(os.path.join(cur_dir, '../yaml/test-flow.yml')) as fp:
        a = Flow.load_config(fp)

    b = (Flow()
         .add(name='chunk_seg', parallel=3)
         .add(name='wqncode1', parallel=2)
         .add(name='encode2', parallel=2, needs='chunk_seg')
         .join(['wqncode1', 'encode2']))

    a.save_config('test2.yml')

    c = Flow.load_config('test2.yml')

    assert a == b
    assert a == c

    with a as f:
        node = f._pod_nodes['gateway']
        assert node.head_args.socket_in == SocketType.PULL_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['chunk_seg']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.head_args.socket_out == SocketType.ROUTER_BIND
        for arg in node.peas_args['peas']:
            assert arg.socket_in == SocketType.DEALER_CONNECT
            assert arg.socket_out == SocketType.PUSH_CONNECT
        assert node.tail_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUB_BIND

        node = f._pod_nodes['wqncode1']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.head_args.socket_out == SocketType.ROUTER_BIND
        for arg in node.peas_args['peas']:
            assert arg.socket_in == SocketType.DEALER_CONNECT
            assert arg.socket_out == SocketType.PUSH_CONNECT
        assert node.tail_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['encode2']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.head_args.socket_out == SocketType.ROUTER_BIND
        for arg in node.peas_args['peas']:
            assert arg.socket_in == SocketType.DEALER_CONNECT
            assert arg.socket_out == SocketType.PUSH_CONNECT
        assert node.tail_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

    rm_files(['test2.yml'])


def test_dryrun():
    f = (Flow()
         .add(name='dummyEncoder', uses=os.path.join(cur_dir, '../mwu-encoder/mwu_encoder.yml')))

    with f:
        f.dry_run()


def test_pod_status():
    args = set_pod_parser().parse_args(['--parallel', '3'])
    with BasePod(args) as p:
        assert len(p.status) == p.num_peas
        for v in p.status:
            assert v


def test_flow_no_container():
    f = (Flow()
         .add(name='dummyEncoder', uses=os.path.join(cur_dir, '../mwu-encoder/mwu_encoder.yml')))

    with f:
        f.index(input_fn=random_docs(10))


def test_flow_yaml_dump():
    f = Flow(logserver_config=os.path.join(cur_dir, '../yaml/test-server-config.yml'),
             optimize_level=FlowOptimizeLevel.IGNORE_GATEWAY,
             no_gateway=True)
    f.save_config('test1.yml')

    fl = Flow.load_config('test1.yml')
    assert f.args.logserver_config == fl.args.logserver_config
    assert f.args.optimize_level == fl.args.optimize_level
    rm_files(['test1.yml'])


def test_flow_log_server():
    f = Flow.load_config(os.path.join(cur_dir, '../yaml/test_log_server.yml'))
    with f:
        assert hasattr(JINA_GLOBAL.logserver, 'ready')

        # Ready endpoint
        a = requests.get(
            JINA_GLOBAL.logserver.address +
            '/status/ready',
            timeout=5)
        assert a.status_code == 200

        # YAML endpoint
        a = requests.get(
            JINA_GLOBAL.logserver.address +
            '/data/yaml',
            timeout=5)
        assert a.text.startswith('!Flow')
        assert a.status_code == 200

        # Pod endpoint
        a = requests.get(
            JINA_GLOBAL.logserver.address +
            '/data/api/pod',
            timeout=5)
        assert 'pod' in a.json()
        assert a.status_code == 200

        # Shutdown endpoint
        a = requests.get(
            JINA_GLOBAL.logserver.address +
            '/action/shutdown',
            timeout=5)
        assert a.status_code == 200

        # Check ready endpoint after shutdown, check if server stopped
        with pytest.raises(requests.exceptions.ConnectionError):
            requests.get(
                JINA_GLOBAL.logserver.address +
                '/status/ready',
                timeout=5)


def test_shards():
    f = Flow().add(name='doc_pb', uses=os.path.join(cur_dir, '../yaml/test-docpb.yml'), parallel=3,
                   separated_workspace=True)
    with f:
        f.index(input_fn=random_docs(1000), random_doc_id=False)
    with f:
        pass
    rm_files(['test-docshard-tmp'])


def test_py_client():
    f = (Flow().add(name='r1')
         .add(name='r2')
         .add(name='r3', needs='r1')
         .add(name='r4', needs='r2')
         .add(name='r5', needs='r3')
         .add(name='r6', needs='r4')
         .add(name='r8', needs='r6')
         .add(name='r9', needs='r5')
         .add(name='r10', needs=['r9', 'r8']))

    with f:
        f.dry_run()
        from jina.clients import py_client
        py_client(port_expose=f.port_expose, host=f.host).dry_run(IndexDryRunRequest())

    with f:
        node = f._pod_nodes['gateway']
        assert node.head_args.socket_in == SocketType.PULL_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r1']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUB_BIND

        node = f._pod_nodes['r2']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r3']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r4']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r5']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r6']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r8']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r9']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r10']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_BIND

        for name, node in f._pod_nodes.items():
            assert node.peas_args['peas'][0] == node.head_args
            assert node.peas_args['peas'][0] == node.tail_args


def test_dry_run_with_two_pathways_diverging_at_gateway():
    f = (Flow().add(name='r2')
         .add(name='r3', needs='gateway')
         .join(['r2', 'r3']))

    with f:
        node = f._pod_nodes['gateway']
        assert node.head_args.socket_in == SocketType.PULL_CONNECT
        assert node.tail_args.socket_out == SocketType.PUB_BIND

        node = f._pod_nodes['r2']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r3']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        for name, node in f._pod_nodes.items():
            assert node.peas_args['peas'][0] == node.head_args
            assert node.peas_args['peas'][0] == node.tail_args

        f.dry_run()


def test_dry_run_with_two_pathways_diverging_at_non_gateway():
    f = (Flow().add(name='r1')
         .add(name='r2')
         .add(name='r3', needs='r1')
         .join(['r2', 'r3']))

    with f:
        node = f._pod_nodes['gateway']
        assert node.head_args.socket_in == SocketType.PULL_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r1']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUB_BIND

        node = f._pod_nodes['r2']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r3']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        for name, node in f._pod_nodes.items():
            assert node.peas_args['peas'][0] == node.head_args
            assert node.peas_args['peas'][0] == node.tail_args
        f.dry_run()


def test_refactor_num_part():
    f = (Flow().add(name='r1', uses='_logforward', needs='gateway')
         .add(name='r2', uses='_logforward', needs='gateway')
         .join(['r1', 'r2']))

    with f:
        node = f._pod_nodes['gateway']
        assert node.head_args.socket_in == SocketType.PULL_CONNECT
        assert node.tail_args.socket_out == SocketType.PUB_BIND

        node = f._pod_nodes['r1']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r2']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        for name, node in f._pod_nodes.items():
            assert node.peas_args['peas'][0] == node.head_args
            assert node.peas_args['peas'][0] == node.tail_args


def test_refactor_num_part_proxy():
    f = (Flow().add(name='r1', uses='_logforward')
         .add(name='r2', uses='_logforward', needs='r1')
         .add(name='r3', uses='_logforward', needs='r1')
         .join(['r2', 'r3']))

    with f:
        node = f._pod_nodes['gateway']
        assert node.head_args.socket_in == SocketType.PULL_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r1']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUB_BIND

        node = f._pod_nodes['r2']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r3']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        for name, node in f._pod_nodes.items():
            assert node.peas_args['peas'][0] == node.head_args
            assert node.peas_args['peas'][0] == node.tail_args


def test_refactor_num_part_proxy_2():
    f = (Flow().add(name='r1', uses='_logforward')
         .add(name='r2', uses='_logforward', needs='r1', parallel=2)
         .add(name='r3', uses='_logforward', needs='r1', parallel=3, polling='ALL')
         .needs(['r2', 'r3']))

    with f:
        f.index_lines(lines=['abbcs', 'efgh'])


def test_refactor_num_part_2():
    f = (Flow()
         .add(name='r1', uses='_logforward', needs='gateway', parallel=3, polling='ALL'))

    with f:
        f.index_lines(lines=['abbcs', 'efgh'])

    f = (Flow()
         .add(name='r1', uses='_logforward', needs='gateway', parallel=3))

    with f:
        f.index_lines(lines=['abbcs', 'efgh'])


def test_index_text_files():
    def validate(req):
        for d in req.docs:
            assert d.text

    f = (Flow(read_only=True).add(uses=os.path.join(cur_dir, '../yaml/datauriindex.yml'), timeout_ready=-1))

    with f:
        f.index_files('*.py', output_fn=validate, callback_on='body')

    rm_files(['doc.gzip'])


def test_flow_with_publish_driver():
    f = (Flow()
         .add(name='r2', uses='!OneHotTextEncoder')
         .add(name='r3', uses='!OneHotTextEncoder', needs='gateway')
         .join(needs=['r2', 'r3']))

    def validate(req):
        for d in req.docs:
            assert d.embedding is not None

    with f:
        f.index_lines(lines=['text_1', 'text_2'], output_fn=validate)


def test_flow_with_modalitys_simple():
    def validate(req):
        for d in req.index.docs:
            assert d.modality in ['mode1', 'mode2']

    def input_fn():
        doc1 = DocumentProto()
        doc1.modality = 'mode1'
        doc2 = DocumentProto()
        doc2.modality = 'mode2'
        doc3 = DocumentProto()
        doc3.modality = 'mode1'
        return [doc1, doc2, doc3]

    flow = Flow().add(name='chunk_seg', parallel=3). \
        add(name='encoder12', parallel=2,
            uses='- !FilterQL | {lookups: {modality__in: [mode1, mode2]}, traversal_paths: [c]}')
    with flow:
        flow.index(input_fn=input_fn, output_fn=validate)


def test_load_flow_with_port():
    f = Flow.load_config('yaml/test-flow-port.yml')
    with f:
        assert f.port_expose == 12345


def test_load_flow_from_cli():
    a = set_flow_parser().parse_args(['--uses', 'yaml/test-flow-port.yml'])
    f = Flow.load_config(a.uses)
    with f:
        assert f.port_expose == 12345


def test_flow_arguments_priorities():
    f = Flow(port_expose=12345).add(name='test', port_expose=23456)
    assert '23456' in f._pod_nodes['test'].cli_args
    assert '12345' not in f._pod_nodes['test'].cli_args


def test_flow_default_argument_passing():
    f = Flow(port_expose=12345).add(name='test')
    assert '12345' in f._pod_nodes['test'].cli_args


def test_flow_arbitrary_needs():
    f = (Flow().add(name='p1').add(name='p2', needs='gateway')
         .add(name='p3', needs='gateway')
         .add(name='p4', needs='gateway')
         .add(name='p5', needs='gateway')
         .needs(['p2', 'p4'], name='r1')
         .needs(['p3', 'p5'], name='r2')
         .needs(['p1', 'r1'], name='r3')
         .needs(['r2', 'r3'], name='r4'))

    with f:
        f.index_lines(['abc', 'def'])


def test_flow_needs_all():
    f = (Flow().add(name='p1', needs='gateway')
         .needs_all(name='r1'))
    assert f._pod_nodes['r1'].needs == {'p1'}

    f = (Flow().add(name='p1', needs='gateway')
         .add(name='p2', needs='gateway')
         .add(name='p3', needs='gateway')
         .needs(needs=['p1', 'p2'], name='r1')
         .needs_all(name='r2'))
    assert f._pod_nodes['r2'].needs == {'p3', 'r1'}

    with f:
        f.index_ndarray(np.random.random([10, 10]))

    f = (Flow().add(name='p1', needs='gateway')
         .add(name='p2', needs='gateway')
         .add(name='p3', needs='gateway')
         .needs(needs=['p1', 'p2'], name='r1')
         .needs_all(name='r2')
         .add(name='p4', needs='r2'))
    assert f._pod_nodes['r2'].needs == {'p3', 'r1'}
    assert f._pod_nodes['p4'].needs == {'r2'}

    with f:
        f.index_ndarray(np.random.random([10, 10]))

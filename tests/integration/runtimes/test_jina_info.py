import multiprocessing
import time

import grpc
import pytest
import requests

from jina import __jina_env__, __version__
from jina.proto import jina_pb2, jina_pb2_grpc
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.worker import WorkerRuntime
from tests.helper import _generate_pod_args

from .test_runtimes import _create_gateway_runtime, _create_head_runtime


def _create_worker_runtime(port, name='', executor=None):
    args = _generate_pod_args()
    args.port = port
    args.name = name
    if executor:
        args.uses = executor
    with WorkerRuntime(args) as runtime:
        runtime.run_forever()


def _create_worker(port):
    # create a single worker runtime
    p = multiprocessing.Process(target=_create_worker_runtime, args=(port,))
    p.start()
    time.sleep(0.1)
    return p


def _create_gateway(port, graph, pod_addr, protocol):
    # create a single worker runtime
    # create a single gateway runtime
    p = multiprocessing.Process(
        target=_create_gateway_runtime,
        args=(graph, pod_addr, port, protocol),
    )
    p.start()
    time.sleep(0.1)
    return p


def _create_head(port, connection_list_dict, polling='ANY'):
    p = multiprocessing.Process(
        target=_create_head_runtime, args=(port, connection_list_dict, 'head', polling)
    )
    p.start()
    time.sleep(0.1)
    return p


@pytest.mark.parametrize('runtime', ['head', 'worker', 'gateway'])
def test_jina_info_grpc_based_runtimes(runtime, port_generator):
    port = port_generator()
    connection_list_dict = {}
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{port}"]}}'
    if runtime == 'head':
        p = _create_head(port, connection_list_dict)
    elif runtime == 'gateway':
        p = _create_gateway(port, graph_description, pod_addresses, 'grpc')
    else:
        p = _create_worker(port)

    try:
        AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
            timeout=5.0,
            ctrl_address=f'0.0.0.0:{port}',
            ready_or_shutdown_event=multiprocessing.Event(),
        )

        channel = grpc.insecure_channel(f'localhost:{port}')
        stub = jina_pb2_grpc.JinaInfoRPCStub(channel)
        res = stub._status(
            jina_pb2.google_dot_protobuf_dot_empty__pb2.Empty(),
        )
        assert res.jina['jina'] == __version__
        for env_var in __jina_env__:
            assert env_var in res.envs
    except Exception:
        assert False
    finally:
        p.terminate()
        p.join()


@pytest.mark.parametrize('protocol', ['http', 'websocket'])
def test_jina_info_gateway_http(protocol, port_generator):
    port = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{port}"]}}'
    p = _create_gateway(port, graph_description, pod_addresses, protocol)

    try:
        AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
            timeout=5.0,
            ctrl_address=f'0.0.0.0:{port}',
            ready_or_shutdown_event=multiprocessing.Event(),
        )

        x = requests.get(f'http://localhost:{port}/status')
        resp = x.json()
        assert 'jina' in resp
        assert 'envs' in resp
        assert resp['jina']['jina'] == __version__
        for env_var in __jina_env__:
            assert env_var in resp['envs']
    except Exception:
        assert False
    finally:
        p.terminate()
        p.join()

import os
import time
import multiprocessing
import pytest
from docarray import DocumentArray

from jina import Flow
from jina.helper import random_port
from jina.orchestrate.deployments import Deployment
from jina.parsers import set_deployment_parser

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def replica_docker_image_built():
    import docker

    client = docker.from_env()
    client.images.build(path=cur_dir, tag='worker-runtime')
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()


@pytest.fixture(scope='function')
def input_docs():
    return DocumentArray.empty(50)


def _external_deployment_args(num_shards, port=None):
    args = [
        '--uses',
        os.path.join(cur_dir, 'config.yml'),
        '--name',
        'external_real',
        '--port',
        str(port) if port else str(random_port()),
        '--host-in',
        '0.0.0.0',
        '--shards',
        str(num_shards),
        '--polling',
        'all',
    ]
    return set_deployment_parser().parse_args(args)


def _external_deployment_args_docker(num_shards, port=None):
    args = [
        '--uses',
        'docker://worker-runtime',
        '--name',
        'external_real',
        '--port',
        str(port) if port else str(random_port()),
        '--host-in',
        '0.0.0.0',
        '--shards',
        str(num_shards),
        '--polling',
        'all',
    ]
    return set_deployment_parser().parse_args(args)


def _start_deployment_in_process_and_communicate_start(depl_args, start_signal, end_signal):
    def _f(args, s_signal, e_signal):
        with Deployment(args):
            s_signal.set()
            e_signal.wait()

    process = multiprocessing.Process(target=_f, args=(depl_args, start_signal, end_signal))
    process.start()
    return process


@pytest.mark.parametrize(
    'hosts', ['localhost,localhost', ['localhost', 'localhost'], 'localhost']
)
@pytest.mark.parametrize('as_list', [True, False])
@pytest.mark.parametrize('stream', [False, True])
def test_distributed_replicas(input_docs, hosts, as_list, stream):
    port1, port2 = random_port(), random_port()
    ports = [port1, port2]
    if not as_list:
        ports = f'{port1},{port2}'
    args1, args2 = _external_deployment_args(
        num_shards=1, port=port1
    ), _external_deployment_args(num_shards=1, port=port2)
    start_signal1 = multiprocessing.Event()
    start_signal2 = multiprocessing.Event()
    end_signal = multiprocessing.Event()
    p1 = _start_deployment_in_process_and_communicate_start(args1, start_signal1, end_signal)
    p2 = _start_deployment_in_process_and_communicate_start(args2, start_signal2, end_signal)
    try:
        start_signal1.wait(timeout=50)
        start_signal2.wait(timeout=50)
        flow = Flow().add(
            host=hosts,
            port=ports,
            external=True,
        )
        with flow:
            resp = flow.index(inputs=input_docs, request_size=2, stream=stream)

        end_signal.set()

        depl1_id = resp[0].tags['uuid']
        assert any([depl1_id != depl_id for depl_id in resp[1:, 'tags__uuid']])
    except:
        raise
    finally:
        p1.kill()
        p2.kill()


def test_distributed_replicas_hosts_mismatch(input_docs):
    ports = [random_port(), random_port()]
    args1, args2 = _external_deployment_args(
        num_shards=1, port=ports[0]
    ), _external_deployment_args(num_shards=1, port=ports[1])
    depl1 = Deployment(args1)
    depl2 = Deployment(args2)
    with depl1, depl2:
        with pytest.raises(ValueError) as err_info:
            flow = Flow().add(
                host=['localhost', 'localhost'],
                port=ports,
                external=True,
                replicas=3,
            )
            with flow:
                pass
    assert (
            'Number of hosts (2) does not match the number of replicas (3)'
            in err_info.value.args[0]
    )


@pytest.mark.parametrize(
    'hosts_as_list',
    [True, False],
)
@pytest.mark.parametrize(
    'ports_as_list',
    [True, False],
)
def test_distributed_replicas_host_parsing(input_docs, hosts_as_list, ports_as_list):
    port1, port2 = random_port(), random_port()
    args1, args2 = _external_deployment_args(
        num_shards=1, port=port1
    ), _external_deployment_args(num_shards=1, port=port2)
    depl1 = Deployment(args1)
    depl2 = Deployment(args2)
    if ports_as_list:
        ports = [port1, port2]
    else:
        ports = f'{port1},{port2}'

    if hosts_as_list:
        hosts = [f'localhost:{port1}', f'localhost:{port2}']
    else:
        hosts = f'localhost:{port1},localhost:{port2}'

    with depl1, depl2:
        flow = Flow().add(
            host=hosts,
            port=ports,
            external=True,
        )
        with flow:
            resp = flow.index(inputs=input_docs, request_size=2)

        depl1_id = resp[0].tags['uuid']
        assert any([depl1_id != depl_id for depl_id in resp[1:, 'tags__uuid']])


@pytest.mark.parametrize(
    'hosts', ['localhost,localhost', ['localhost', 'localhost'], 'localhost']
)
@pytest.mark.parametrize(
    'ports_as_list',
    [True, False],
)
def test_distributed_replicas_docker(
        input_docs, hosts, ports_as_list, replica_docker_image_built
):
    port1, port2 = random_port(), random_port()
    args1, args2 = _external_deployment_args_docker(
        num_shards=1, port=port1
    ), _external_deployment_args_docker(num_shards=1, port=port2)
    depl1 = Deployment(args1)
    depl2 = Deployment(args2)

    if ports_as_list:
        ports = [port1, port2]
    else:
        ports = f'{port1},{port2}'
    with depl1, depl2:
        flow = Flow().add(
            host=hosts,
            port=ports,
            external=True,
        )
        with flow:
            resp = flow.index(inputs=input_docs, request_size=2)

        depl1_id = resp[0].tags['uuid']
        assert any([depl1_id != depl_id for depl_id in resp[1:, 'tags__uuid']])

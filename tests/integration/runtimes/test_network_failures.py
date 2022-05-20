import multiprocessing
import time

import pytest

from jina import Client, Document, Executor, requests
from jina.parsers import set_gateway_parser, set_pod_parser
from jina.serve.networking import GrpcConnectionPool
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.gateway.http import HTTPGatewayRuntime
from jina.serve.runtimes.worker import WorkerRuntime
from jina.types.request.control import ControlRequest

from .test_runtimes import _create_gateway_runtime, _create_head_runtime


class DummyExec(Executor):
    @requests(on='/foo')
    def foo(self, *args, **kwargs):
        pass


def _create_worker_runtime(port, name='', executor=None):
    args = set_pod_parser().parse_args([])
    args.port = port
    args.uses = 'DummyExec'
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


def _create_head(port, polling):
    p = multiprocessing.Process(
        target=_create_head_runtime, args=(port, 'head', polling)
    )
    p.start()
    time.sleep(0.1)
    return p


def _send_request(gateway_port, protocol):
    """send request to gateway and see what happens"""
    c = Client(host='localhost', port=gateway_port, protocol=protocol)
    return c.post(
        '/foo',
        inputs=[Document(text='hi') for _ in range(2)],
        request_size=1,
        return_responses=True,
    )


def _test_error(gateway_port, error_ports, protocol):
    if not isinstance(error_ports, list):
        error_ports = [error_ports]
    with pytest.raises(ConnectionError) as err_info:  # assert correct error is thrown
        _send_request(gateway_port, protocol)
    # assert error message contains the port(s) of the broken executor(s)
    for port in error_ports:
        assert str(port) in err_info.value.args[0]


@pytest.mark.parametrize(
    'fail_before_endpoint_discovery', [True, False]
)  # if not before, then after
@pytest.mark.parametrize('protocol', ['http', 'websocket', 'grpc'])
@pytest.mark.asyncio
async def test_runtimes_headless_topology(
    port_generator, protocol, fail_before_endpoint_discovery
):
    # create gateway and workers manually, then terminate worker process to provoke an error
    worker_port = port_generator()
    gateway_port = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{worker_port}"]}}'

    worker_process = _create_worker(worker_port)
    gateway_process = _create_gateway(
        gateway_port, graph_description, pod_addresses, protocol
    )

    time.sleep(1.0)

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{worker_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{gateway_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    if (
        fail_before_endpoint_discovery
    ):  # kill worker before having sent the first request, so before endpoint discov.
        worker_process.terminate()
        worker_process.join()

    try:
        if fail_before_endpoint_discovery:
            # here worker is already dead before the first request, so endpoint discovery will fail
            # ----------- 1. test that useful errors are given when endpoint discovery fails -----------
            # we have to do this in a new process because otherwise grpc will be sad and everything will crash :(
            p = multiprocessing.Process(
                target=_test_error, args=(gateway_port, worker_port, protocol)
            )
            p.start()
            p.join()
            assert (
                p.exitcode == 0
            )  # if exitcode != 0 then test in other process did not pass and this should fail
        else:
            # just ping the Flow without having killed a worker before. This (also) performs endpoint discovery
            p = multiprocessing.Process(
                target=_send_request, args=(gateway_port, protocol)
            )
            p.start()
            p.join()
            # only now do we kill the worker, after having performed successful endpoint discovery
            # so in this case, the actual request will fail, not the discovery, which is handled differently by Gateway
            worker_process.terminate()  # kill worker
            worker_process.join()
            assert not worker_process.is_alive()
        # ----------- 2. test that gateways remain alive -----------
        # just do the same again, expecting the same failure
        p = multiprocessing.Process(
            target=_test_error, args=(gateway_port, worker_port, protocol)
        )
        p.start()
        p.join()
        assert (
            p.exitcode == 0
        )  # if exitcode != 0 then test in other process did not pass and this should fail
    except Exception:
        assert False
    finally:  # clean up runtimes
        gateway_process.terminate()
        worker_process.terminate()
        gateway_process.join()
        worker_process.join()


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
@pytest.mark.asyncio
async def test_runtimes_replicas(port_generator, protocol):
    # create gateway and workers manually, then terminate worker process to provoke an error
    worker_ports = [port_generator() for _ in range(3)]
    worker0_port, worker1_port, worker2_port = worker_ports
    gateway_port = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{worker0_port}", "0.0.0.0:{worker1_port}", "0.0.0.0:{worker2_port}"]}}'

    worker_processes = []
    for p in worker_ports:
        worker_processes.append(_create_worker(p))
        time.sleep(0.1)
        AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
            timeout=5.0,
            ctrl_address=f'0.0.0.0:{p}',
            ready_or_shutdown_event=multiprocessing.Event(),
        )

    gateway_process = _create_gateway(
        gateway_port, graph_description, pod_addresses, protocol
    )
    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{gateway_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    worker_processes[0].terminate()  # kill 'middle' worker
    worker_processes[0].join()

    try:
        # await _send_request(gateway_port, protocol)
        # ----------- 1. test that useful errors are given -----------
        # we have to do this in a new process because otherwise grpc will be sad and everything will crash :(
        p = multiprocessing.Process(
            target=_test_error, args=(gateway_port, worker0_port, protocol)
        )
        p.start()
        p.join()
        assert (
            p.exitcode == 0
        )  # if exitcode != 0 then test in other process did not pass and this should fail
        # no retry in the case with replicas, because round robin retry mechanism will pick different replica now
    except Exception:
        assert False
    finally:  # clean up runtimes
        gateway_process.terminate()
        gateway_process.join()
        for p in worker_processes:
            p.terminate()
            p.join()


@pytest.mark.parametrize('terminate_head', [True, False])
@pytest.mark.parametrize('protocol', ['http', 'websocket', 'grpc'])
@pytest.mark.asyncio
async def test_runtimes_headful_topology(port_generator, protocol, terminate_head):
    # create gateway and workers manually, then terminate worker process to provoke an error
    worker_port = port_generator()
    gateway_port = port_generator()
    head_port = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    head_process = _create_head(head_port, 'ANY')
    worker_process = _create_worker(worker_port)
    gateway_process = _create_gateway(
        gateway_port, graph_description, pod_addresses, protocol
    )

    time.sleep(1.0)

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{head_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{worker_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{gateway_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    # this would be done by the Pod, its adding the worker to the head
    activate_msg = ControlRequest(command='ACTIVATE')
    activate_msg.add_related_entity('worker', '127.0.0.1', worker_port)
    GrpcConnectionPool.send_request_sync(activate_msg, f'127.0.0.1:{head_port}')

    # terminate pod, either head or worker behind the head
    if terminate_head:
        head_process.terminate()
        head_process.join()
        error_port = head_port
    else:
        worker_process.terminate()  # kill worker
        worker_process.join()
        error_port = worker_port
    error_port = (
        head_port if protocol == 'websocket' else error_port
    )  # due to error msg length constraints ws will always report the head address

    try:
        # ----------- 1. test that useful errors are given -----------
        # we have to do this in a new process because otherwise grpc will be sad and everything will crash :(
        p = multiprocessing.Process(
            target=_test_error, args=(gateway_port, error_port, protocol)
        )
        p.start()
        p.join()
        assert (
            p.exitcode == 0
        )  # if exitcode != 0 then test in other process did not pass and this should fail
        # ----------- 2. test that gateways remain alive -----------
        # just do the same again, expecting the same outcome
        p = multiprocessing.Process(
            target=_test_error, args=(gateway_port, error_port, protocol)
        )
        p.start()
        p.join()
        assert (
            p.exitcode == 0
        )  # if exitcode != 0 then test in other process did not pass and this should fail
    except Exception:
        raise
    finally:  # clean up runtimes
        gateway_process.terminate()
        worker_process.terminate()
        head_process.terminate()
        gateway_process.join()
        worker_process.join()
        head_process.join()


def _send_gql_request(gateway_port):
    """send request to gateway and see what happens"""
    mutation = (
        f'mutation {{'
        + '''docs(data: {text: "abcd"}) { 
                    id 
                } 
            }
    '''
    )
    c = Client(host='localhost', port=gateway_port, protocol='http')
    return c.mutate(mutation=mutation)


def _test_gql_error(gateway_port, error_port):
    with pytest.raises(ConnectionError) as err_info:  # assert correct error is thrown
        _send_gql_request(gateway_port)
    # assert error message contains useful info
    assert str(error_port) in err_info.value.args[0]


def _create_gqlgateway_runtime(graph_description, pod_addresses, port):
    with HTTPGatewayRuntime(
        set_gateway_parser().parse_args(
            [
                '--graph-description',
                graph_description,
                '--deployments-addresses',
                pod_addresses,
                '--port',
                str(port),
                '--expose-graphql-endpoint',
            ]
        )
    ) as runtime:
        runtime.run_forever()


def _create_gqlgateway(port, graph, pod_addr):
    # create a single worker runtime
    # create a single gateway runtime
    p = multiprocessing.Process(
        target=_create_gqlgateway_runtime,
        args=(graph, pod_addr, port),
    )
    p.start()
    time.sleep(0.1)
    return p


@pytest.mark.asyncio
async def test_runtimes_graphql(port_generator):
    # create gateway and workers manually, then terminate worker process to provoke an error
    protocol = 'http'
    worker_port = port_generator()
    gateway_port = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{worker_port}"]}}'

    worker_process = _create_worker(worker_port)
    gateway_process = _create_gqlgateway(gateway_port, graph_description, pod_addresses)

    time.sleep(1.0)

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{worker_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{gateway_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    worker_process.terminate()  # kill worker
    worker_process.join()

    try:
        # ----------- 1. test that useful errors are given -----------
        # we have to do this in a new process because otherwise grpc will be sad and everything will crash :(
        p = multiprocessing.Process(
            target=_test_gql_error, args=(gateway_port, worker_port)
        )
        p.start()
        p.join()
        assert (
            p.exitcode == 0
        )  # if exitcode != 0 then test in other process did not pass and this should fail
        # ----------- 2. test that gateways remain alive -----------
        # just do the same again, expecting the same outcome
        p = multiprocessing.Process(
            target=_test_gql_error, args=(gateway_port, worker_port)
        )
        p.start()
        p.join()
        assert (
            p.exitcode == 0
        )  # if exitcode != 0 then test in other process did not pass and this should fail
    except Exception:
        raise
    finally:  # clean up runtimes
        gateway_process.terminate()
        worker_process.terminate()
        gateway_process.join()
        worker_process.join()


@pytest.mark.asyncio
async def test_replica_retry(port_generator):
    # test that if one replica is down, the other replica(s) will be used
    # create gateway and workers manually, then terminate worker process to provoke an error
    worker_ports = [port_generator() for _ in range(3)]
    worker0_port, worker1_port, worker2_port = worker_ports
    gateway_port = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{worker0_port}", "0.0.0.0:{worker1_port}", "0.0.0.0:{worker2_port}"]}}'

    worker_processes = []
    for p in worker_ports:
        worker_processes.append(_create_worker(p))
        time.sleep(0.1)
        AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
            timeout=5.0,
            ctrl_address=f'0.0.0.0:{p}',
            ready_or_shutdown_event=multiprocessing.Event(),
        )

    gateway_process = _create_gateway(
        gateway_port, graph_description, pod_addresses, 'grpc'
    )
    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{gateway_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    try:
        # ----------- 1. ping Flow once to trigger endpoint discovery -----------
        # we have to do this in a new process because otherwise grpc will be sad and everything will crash :(
        p = multiprocessing.Process(target=_send_request, args=(gateway_port, 'grpc'))
        p.start()
        p.join()
        assert p.exitcode == 0
        # kill second worker, which would be responsible for the second call (round robin)
        worker_processes[1].terminate()
        worker_processes[1].join()
        # ----------- 2. test that redundant replicas take over -----------
        # we have to do this in a new process because otherwise grpc will be sad and everything will crash :(
        p = multiprocessing.Process(target=_send_request, args=(gateway_port, 'grpc'))
        p.start()
        p.join()
        assert p.exitcode == 0
    except Exception:
        assert False
    finally:  # clean up runtimes
        gateway_process.terminate()
        gateway_process.join()
        for p in worker_processes:
            p.terminate()
            p.join()


@pytest.mark.asyncio
async def test_replica_retry_all_fail(port_generator):
    # test that if one replica is down, the other replica(s) will be used
    # create gateway and workers manually, then terminate worker process to provoke an error
    worker_ports = [port_generator() for _ in range(3)]
    worker0_port, worker1_port, worker2_port = worker_ports
    gateway_port = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{worker0_port}", "0.0.0.0:{worker1_port}", "0.0.0.0:{worker2_port}"]}}'

    worker_processes = []
    for p in worker_ports:
        worker_processes.append(_create_worker(p))
        time.sleep(0.1)
        AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
            timeout=5.0,
            ctrl_address=f'0.0.0.0:{p}',
            ready_or_shutdown_event=multiprocessing.Event(),
        )

    gateway_process = _create_gateway(
        gateway_port, graph_description, pod_addresses, 'grpc'
    )
    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{gateway_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    try:
        # ----------- 1. ping Flow once to trigger endpoint discovery -----------
        # we have to do this in a new process because otherwise grpc will be sad and everything will crash :(
        p = multiprocessing.Process(target=_send_request, args=(gateway_port, 'grpc'))
        p.start()
        p.join()
        assert p.exitcode == 0
        # kill all workers
        for p in worker_processes:
            p.terminate()
            p.join()
        # ----------- 2. test that call fails with informative error message -----------
        # we have to do this in a new process because otherwise grpc will be sad and everything will crash :(
        p = multiprocessing.Process(
            target=_test_error, args=(gateway_port, worker_ports, 'grpc')
        )
        p.start()
        p.join()
        assert p.exitcode == 0
    except Exception:
        assert False
    finally:  # clean up runtimes
        gateway_process.terminate()
        gateway_process.join()
        for p in worker_processes:
            p.terminate()
            p.join()

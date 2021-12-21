import asyncio
import json
import time

import pytest

from jina import Document, Executor, Client, requests
from jina.enums import PollingType
from jina.parsers import set_gateway_parser, set_pod_parser
from jina.peapods import Pod


@pytest.mark.asyncio
# test gateway, head and worker pea by creating them manually in the most simple configuration
async def test_pods_trivial_topology(port_generator):
    pod_port = port_generator()
    port_expose = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{pod_port}"]}}'

    # create a single worker pea
    worker_pod = _create_regular_pod(pod_port)

    # create a single gateway pea
    gateway_pod = _create_gateway_pod(graph_description, pod_addresses, port_expose)

    with gateway_pod, worker_pod:

        # send requests to the gateway
        c = Client(host='localhost', port=port_expose, asyncio=True)
        responses = c.post(
            '/', inputs=async_inputs, request_size=1, return_results=True
        )

        response_list = []
        async for response in responses:
            response_list.append(response)

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1


@pytest.fixture
def complete_graph_dict():
    return {
        'start-gateway': ['pod0', 'pod4', 'pod6'],
        'pod0': ['pod1', 'pod2'],
        'pod1': ['end-gateway'],
        'pod2': ['pod3'],
        'pod4': ['pod5'],
        'merger': ['pod_last'],
        'pod5': ['merger'],
        'pod3': ['merger'],
        'pod6': [],  # hanging_pod
        'pod_last': ['end-gateway'],
    }


@pytest.mark.asyncio
@pytest.mark.parametrize('uses_before', [True, False])
@pytest.mark.parametrize('uses_after', [True, False])
# test gateway, head and worker pea by creating them manually in a more Flow like topology with branching/merging
async def test_pods_flow_topology(
    complete_graph_dict, uses_before, uses_after, port_generator
):
    pods = [
        pod_name for pod_name in complete_graph_dict.keys() if 'gateway' not in pod_name
    ]
    started_pods = []
    pod_addresses = '{'
    for pod in pods:
        head_port = port_generator()
        pod_addresses += f'"{pod}": ["0.0.0.0:{head_port}"],'
        regular_pod = _create_regular_pod(
            port=head_port,
            name=f'{pod}',
            uses_before=uses_before,
            uses_after=uses_after,
        )

        started_pods.append(regular_pod)
        regular_pod.start()

    # remove last comma
    pod_addresses = pod_addresses[:-1]
    pod_addresses += '}'
    port_expose = port_generator()

    # create a single gateway pea

    gateway_pod = _create_gateway_pod(
        json.dumps(complete_graph_dict), pod_addresses, port_expose
    )
    gateway_pod.start()

    await asyncio.sleep(0.1)

    # send requests to the gateway
    c = Client(host='localhost', port=port_expose, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_results=True)
    response_list = []
    async for response in responses:
        response_list.append(response)

    # clean up pods
    gateway_pod.close()
    for pod in started_pods:
        pod.close()

    assert len(response_list) == 20
    expected_docs = 1
    if uses_before and uses_after:
        expected_docs = 3 + 1 + 1
    elif uses_before or uses_after:
        expected_docs = 3
    assert len(response_list[0].docs) == expected_docs


@pytest.mark.asyncio
@pytest.mark.parametrize('polling', [PollingType.ALL, PollingType.ANY])
# test simple topology with shards
async def test_pods_shards(polling, port_generator):
    head_port = port_generator()
    port_expose = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    pod = _create_regular_pod(port=head_port, name='pod', polling=polling, shards=10)
    pod.start()

    gateway_pod = _create_gateway_pod(graph_description, pod_addresses, port_expose)
    gateway_pod.start()

    await asyncio.sleep(1.0)

    c = Client(host='localhost', port=port_expose, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_results=True)
    response_list = []
    async for response in responses:
        response_list.append(response)

    gateway_pod.close()
    pod.close()

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1 if polling == PollingType.ANY else 10


@pytest.mark.asyncio
# test simple topology with replicas
async def test_pods_replicas(port_generator):
    head_port = port_generator()
    port_expose = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    pod = _create_regular_pod(port=head_port, name='pod', replicas=10)
    pod.start()

    gateway_pod = _create_gateway_pod(graph_description, pod_addresses, port_expose)
    gateway_pod.start()

    await asyncio.sleep(1.0)

    c = Client(host='localhost', port=port_expose, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_results=True)
    response_list = []
    async for response in responses:
        response_list.append(response)

    gateway_pod.close()
    pod.close()

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1


@pytest.mark.asyncio
async def test_pods_with_executor(port_generator):
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'

    head_port = port_generator()
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    regular_pod = _create_regular_pod(
        port=head_port,
        name='pod',
        executor='NameChangeExecutor',
        uses_before=True,
        uses_after=True,
        polling=PollingType.ALL,
    )
    regular_pod.start()

    port_expose = port_generator()
    gateway_pod = _create_gateway_pod(graph_description, pod_addresses, port_expose)
    gateway_pod.start()

    await asyncio.sleep(1.0)

    c = Client(host='localhost', port=port_expose, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_results=True)
    response_list = []
    async for response in responses:
        response_list.append(response.docs)

    gateway_pod.close()
    regular_pod.close()

    assert len(response_list) == 20
    assert len(response_list[0]) == 4

    doc_texts = [doc.text for doc in response_list[0]]
    assert doc_texts.count('client0-Request') == 1
    assert doc_texts.count('pod/uses_before-0') == 1
    assert doc_texts.count('pod/uses_after-0') == 1


@pytest.mark.asyncio
async def test_pods_with_replicas_advance_faster(port_generator):
    head_port = port_generator()
    port_expose = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    pod = _create_regular_pod(
        port=head_port, name='pod', executor='FastSlowExecutor', replicas=10
    )
    pod.start()

    gateway_pod = _create_gateway_pod(graph_description, pod_addresses, port_expose)
    gateway_pod.start()

    await asyncio.sleep(1.0)

    c = Client(host='localhost', port=port_expose, asyncio=True)
    input_docs = [Document(text='slow'), Document(text='fast')]
    responses = c.post('/', inputs=input_docs, request_size=1, return_results=True)
    response_list = []
    async for response in responses:
        response_list.append(response)

    gateway_pod.close()
    pod.close()

    assert len(response_list) == 2
    for response in response_list:
        assert len(response.docs) == 1

    assert response_list[0].docs[0].text == 'fast'
    assert response_list[1].docs[0].text == 'slow'


class NameChangeExecutor(Executor):
    def __init__(self, runtime_args, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = runtime_args['name']

    @requests
    def foo(self, docs, **kwargs):
        docs.append(Document(text=self.name))
        return docs


class FastSlowExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            if doc.text == 'slow':
                time.sleep(1.0)


def _create_regular_pod(
    port,
    name='',
    executor=None,
    uses_before=False,
    uses_after=False,
    polling=PollingType.ANY,
    shards=None,
    replicas=None,
):
    args = set_pod_parser().parse_args([])
    args.port_in = port
    args.name = name
    if shards:
        args.shards = shards
    if replicas:
        args.replicas = replicas
    args.polling = polling
    if executor:
        args.uses = executor if executor else 'NameChangeExecutor'
    if uses_after:
        args.uses_after = executor if executor else 'NameChangeExecutor'
    if uses_before:
        args.uses_before = executor if executor else 'NameChangeExecutor'
    return Pod(args)


def _create_gateway_pod(graph_description, pod_addresses, port_expose):
    return Pod(
        set_gateway_parser().parse_args(
            [
                '--graph-description',
                graph_description,
                '--pods-addresses',
                pod_addresses,
                '--port-expose',
                str(port_expose),
            ]
        )
    )


async def async_inputs():
    for _ in range(20):
        yield Document(text='client0-Request')

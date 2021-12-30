import copy
from typing import List

import pytest
import asyncio

from collections import defaultdict

from jina.peapods.runtimes.gateway.graph.topology_graph import TopologyGraph
from jina.types.request import Request
from jina import DocumentArray, Document
from jina.types.request.data import DataRequest


@pytest.fixture
def linear_graph_dict():
    return {
        'start-gateway': ['pod0'],
        'pod0': ['pod1'],
        'pod1': ['pod2'],
        'pod2': ['pod3'],
        'pod3': ['end-gateway'],
    }


@pytest.fixture
def bifurcation_graph_dict():
    return {
        'start-gateway': ['pod0', 'pod4', 'pod6'],
        'pod0': ['pod1', 'pod2'],
        'pod1': [],  # hanging_pod
        'pod2': ['pod3'],
        'pod4': ['pod5'],
        'pod5': ['end-gateway'],
        'pod3': ['end-gateway'],
        'pod6': [],  # hanging_pod
    }


@pytest.fixture
def merge_graph_dict_directly_merge_in_gateway():
    return {
        'start-gateway': ['pod0'],
        'pod0': ['pod1', 'pod2'],
        'pod1': ['merger'],
        'pod2': ['merger'],
        'merger': ['end-gateway'],
    }


@pytest.fixture
def merge_graph_dict_directly_merge_in_last_pod():
    return {
        'start-gateway': ['pod0'],
        'pod0': ['pod1', 'pod2'],
        'pod1': ['merger'],
        'pod2': ['merger'],
        'merger': ['pod_last'],
        'pod_last': ['end-gateway'],
    }


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


@pytest.fixture
def graph_hanging_pod_after_merge():
    return {
        'start-gateway': ['pod0', 'pod4', 'pod6', 'pod8'],
        'pod0': ['pod1', 'pod2'],
        'pod1': [],  # hanging_pod
        'pod2': ['pod3'],
        'pod4': ['pod5'],
        'pod5': ['end-gateway'],
        'pod3': ['end-gateway'],
        'pod6': ['pod7'],
        'pod8': ['pod7'],
        'pod7': ['pod9'],
        'pod9': [],  # hanging_pod
    }


@pytest.fixture
def two_joins_graph():
    return {
        'start-gateway': ['p0', 'p1'],
        'p0': ['joiner_1'],
        'p1': ['joiner_1'],  # hanging_pod
        'joiner_1': ['p2', 'p3'],
        'p2': ['p4'],
        'p3': ['p4'],
        'p4': ['end-gateway'],
    }


def test_topology_graph_build_linear(linear_graph_dict):
    graph = TopologyGraph(linear_graph_dict)
    assert [node.name for node in graph.origin_nodes] == ['pod0']
    node_pod0 = graph.origin_nodes[0]
    assert node_pod0.name == 'pod0'
    assert node_pod0.number_of_parts == 1
    assert len(node_pod0.outgoing_nodes) == 1
    assert not node_pod0.hanging

    node_pod1 = node_pod0.outgoing_nodes[0]
    assert node_pod1.name == 'pod1'
    assert node_pod1.number_of_parts == 1
    assert len(node_pod1.outgoing_nodes) == 1
    assert not node_pod1.hanging

    node_pod2 = node_pod1.outgoing_nodes[0]
    assert node_pod2.name == 'pod2'
    assert node_pod2.number_of_parts == 1
    assert len(node_pod2.outgoing_nodes) == 1
    assert not node_pod2.hanging

    node_pod3 = node_pod2.outgoing_nodes[0]
    assert node_pod3.name == 'pod3'
    assert node_pod3.number_of_parts == 1
    assert len(node_pod3.outgoing_nodes) == 0
    assert not node_pod3.hanging


def test_topology_graph_build_bifurcation(bifurcation_graph_dict):
    graph = TopologyGraph(bifurcation_graph_dict)
    node_names_list = [node.name for node in graph.origin_nodes]
    assert set(node_names_list) == {'pod0', 'pod4', 'pod6'}
    assert len(graph.origin_nodes[node_names_list.index('pod0')].outgoing_nodes) == 2
    assert set(
        [
            node.name
            for node in graph.origin_nodes[node_names_list.index('pod0')].outgoing_nodes
        ]
    ) == {'pod1', 'pod2'}

    node_pod0 = graph.origin_nodes[node_names_list.index('pod0')]
    assert not node_pod0.hanging
    assert node_pod0.name == 'pod0'
    assert node_pod0.number_of_parts == 1
    outgoing_pod0_list = [node.name for node in node_pod0.outgoing_nodes]

    node_pod1 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod1')]
    assert node_pod1.name == 'pod1'
    assert node_pod1.number_of_parts == 1
    assert len(node_pod1.outgoing_nodes) == 0
    assert node_pod1.hanging

    node_pod2 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod2')]
    assert node_pod2.name == 'pod2'
    assert node_pod2.number_of_parts == 1
    assert len(node_pod2.outgoing_nodes) == 1
    assert not node_pod2.hanging

    node_pod3 = node_pod2.outgoing_nodes[0]
    assert node_pod3.name == 'pod3'
    assert node_pod3.number_of_parts == 1
    assert len(node_pod3.outgoing_nodes) == 0
    assert not node_pod3.hanging

    node_pod4 = graph.origin_nodes[node_names_list.index('pod4')]
    assert node_pod4.name == 'pod4'
    assert node_pod4.number_of_parts == 1
    assert len(node_pod4.outgoing_nodes) == 1
    assert not node_pod4.hanging
    assert set(
        [
            node.name
            for node in graph.origin_nodes[node_names_list.index('pod4')].outgoing_nodes
        ]
    ) == {'pod5'}

    node_pod5 = node_pod4.outgoing_nodes[0]
    assert node_pod5.name == 'pod5'
    assert node_pod5.number_of_parts == 1
    assert not node_pod5.hanging
    assert len(node_pod5.outgoing_nodes) == 0

    node_pod6 = graph.origin_nodes[node_names_list.index('pod6')]
    assert node_pod6.name == 'pod6'
    assert len(node_pod6.outgoing_nodes) == 0
    assert node_pod6.number_of_parts == 1
    assert node_pod6.hanging
    assert set([node.name for node in node_pod6.outgoing_nodes]) == set()


def test_topology_graph_build_merge_in_gateway(
    merge_graph_dict_directly_merge_in_gateway,
):
    graph = TopologyGraph(merge_graph_dict_directly_merge_in_gateway)
    assert set([node.name for node in graph.origin_nodes]) == {'pod0'}

    node_pod0 = graph.origin_nodes[0]
    assert node_pod0.name == 'pod0'
    assert not node_pod0.hanging
    assert len(node_pod0.outgoing_nodes) == 2
    outgoing_pod0_list = [node.name for node in node_pod0.outgoing_nodes]
    assert node_pod0.number_of_parts == 1

    node_pod1 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod1')]
    assert node_pod1.name == 'pod1'
    assert len(node_pod1.outgoing_nodes) == 1
    assert node_pod1.outgoing_nodes[0].name == 'merger'
    assert node_pod1.number_of_parts == 1
    assert not node_pod1.hanging

    node_pod2 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod2')]
    assert node_pod2.name == 'pod2'
    assert len(node_pod2.outgoing_nodes) == 1
    assert node_pod2.outgoing_nodes[0].name == 'merger'
    assert node_pod2.number_of_parts == 1
    assert not node_pod2.hanging
    assert id(node_pod1.outgoing_nodes[0]) == id(node_pod2.outgoing_nodes[0])

    merger_pod = node_pod1.outgoing_nodes[0]
    assert merger_pod.name == 'merger'
    assert merger_pod.number_of_parts == 2
    assert len(merger_pod.outgoing_nodes) == 0
    assert not merger_pod.hanging


def test_topology_graph_build_merge_in_last_pod(
    merge_graph_dict_directly_merge_in_last_pod,
):
    graph = TopologyGraph(merge_graph_dict_directly_merge_in_last_pod)
    assert set([node.name for node in graph.origin_nodes]) == {'pod0'}

    node_pod0 = graph.origin_nodes[0]
    assert node_pod0.number_of_parts == 1
    assert len(node_pod0.outgoing_nodes) == 2
    assert not node_pod0.hanging
    outgoing_pod0_list = [node.name for node in node_pod0.outgoing_nodes]

    node_pod1 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod1')]
    assert node_pod1.number_of_parts == 1
    assert len(node_pod1.outgoing_nodes) == 1
    assert node_pod1.outgoing_nodes[0].name == 'merger'
    assert not node_pod1.hanging

    node_pod2 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod2')]
    assert node_pod2.number_of_parts == 1
    assert len(node_pod2.outgoing_nodes) == 1
    assert node_pod2.outgoing_nodes[0].name == 'merger'
    assert not node_pod2.hanging

    assert id(node_pod1.outgoing_nodes[0]) == id(node_pod2.outgoing_nodes[0])

    merger_pod = node_pod1.outgoing_nodes[0]
    assert merger_pod.name == 'merger'
    assert len(merger_pod.outgoing_nodes) == 1
    assert merger_pod.number_of_parts == 2
    assert not merger_pod.hanging

    pod_last_pod = merger_pod.outgoing_nodes[0]
    assert pod_last_pod.name == 'pod_last'
    assert len(pod_last_pod.outgoing_nodes) == 0
    assert pod_last_pod.number_of_parts == 1
    assert not pod_last_pod.hanging


def test_topology_graph_build_complete(complete_graph_dict):
    graph = TopologyGraph(complete_graph_dict)
    assert set([node.name for node in graph.origin_nodes]) == {
        'pod0',
        'pod4',
        'pod6',
    }
    node_names_list = [node.name for node in graph.origin_nodes]

    node_pod0 = graph.origin_nodes[node_names_list.index('pod0')]
    assert node_pod0.number_of_parts == 1
    assert not node_pod0.hanging
    outgoing_pod0_list = [node.name for node in node_pod0.outgoing_nodes]

    node_pod1 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod1')]
    assert node_pod1.number_of_parts == 1
    assert not node_pod1.hanging
    assert len(node_pod1.outgoing_nodes) == 0

    node_pod2 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod2')]
    assert len(node_pod2.outgoing_nodes) == 1
    assert node_pod2.number_of_parts == 1
    assert not node_pod2.hanging

    node_pod3 = node_pod2.outgoing_nodes[0]
    assert node_pod3.name == 'pod3'
    assert node_pod3.number_of_parts == 1
    assert len(node_pod3.outgoing_nodes) == 1
    assert node_pod3.outgoing_nodes[0].name == 'merger'
    assert not node_pod3.hanging

    node_pod4 = graph.origin_nodes[node_names_list.index('pod4')]
    assert node_pod4.number_of_parts == 1
    assert len(node_pod4.outgoing_nodes) == 1
    assert not node_pod4.hanging

    node_pod5 = node_pod4.outgoing_nodes[0]
    assert node_pod5.number_of_parts == 1
    assert node_pod5.name == 'pod5'
    assert len(node_pod5.outgoing_nodes) == 1
    assert node_pod5.outgoing_nodes[0].name == 'merger'
    assert not node_pod5.hanging

    assert id(node_pod3.outgoing_nodes[0]) == id(node_pod5.outgoing_nodes[0])

    merger_pod = node_pod3.outgoing_nodes[0]
    assert merger_pod.name == 'merger'
    assert len(merger_pod.outgoing_nodes) == 1
    assert merger_pod.number_of_parts == 2
    assert not merger_pod.hanging

    pod_last_pod = merger_pod.outgoing_nodes[0]
    assert pod_last_pod.name == 'pod_last'
    assert len(pod_last_pod.outgoing_nodes) == 0
    assert pod_last_pod.number_of_parts == 1
    assert not pod_last_pod.hanging

    node_pod6 = graph.origin_nodes[node_names_list.index('pod6')]
    assert node_pod6.name == 'pod6'
    assert node_pod6.number_of_parts == 1
    assert len(node_pod6.outgoing_nodes) == 0
    assert node_pod6.hanging


def test_topology_graph_build_hanging_after_merge(graph_hanging_pod_after_merge):
    graph = TopologyGraph(graph_hanging_pod_after_merge)
    node_names_list = [node.name for node in graph.origin_nodes]
    assert set(node_names_list) == {'pod0', 'pod4', 'pod6', 'pod8'}
    assert len(graph.origin_nodes[node_names_list.index('pod0')].outgoing_nodes) == 2
    assert set(
        [
            node.name
            for node in graph.origin_nodes[node_names_list.index('pod0')].outgoing_nodes
        ]
    ) == {'pod1', 'pod2'}

    node_pod0 = graph.origin_nodes[node_names_list.index('pod0')]
    assert node_pod0.name == 'pod0'
    assert node_pod0.number_of_parts == 1
    assert not node_pod0.hanging
    outgoing_pod0_list = [node.name for node in node_pod0.outgoing_nodes]

    node_pod1 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod1')]
    assert node_pod1.name == 'pod1'
    assert node_pod1.number_of_parts == 1
    assert len(node_pod1.outgoing_nodes) == 0
    assert node_pod1.hanging

    node_pod2 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod2')]
    assert node_pod2.name == 'pod2'
    assert node_pod2.number_of_parts == 1
    assert len(node_pod2.outgoing_nodes) == 1
    assert not node_pod2.hanging

    node_pod3 = node_pod2.outgoing_nodes[0]
    assert node_pod3.name == 'pod3'
    assert node_pod3.number_of_parts == 1
    assert len(node_pod3.outgoing_nodes) == 0
    assert not node_pod3.hanging

    node_pod4 = graph.origin_nodes[node_names_list.index('pod4')]
    assert node_pod4.name == 'pod4'
    assert node_pod4.number_of_parts == 1
    assert len(node_pod4.outgoing_nodes) == 1
    assert set(
        [
            node.name
            for node in graph.origin_nodes[node_names_list.index('pod4')].outgoing_nodes
        ]
    ) == {'pod5'}
    assert not node_pod4.hanging

    node_pod5 = node_pod4.outgoing_nodes[0]
    assert node_pod5.name == 'pod5'
    assert node_pod5.number_of_parts == 1
    assert len(node_pod5.outgoing_nodes) == 0
    assert not node_pod5.hanging

    node_pod6 = graph.origin_nodes[node_names_list.index('pod6')]
    assert node_pod6.name == 'pod6'
    assert len(node_pod6.outgoing_nodes) == 1
    assert node_pod6.number_of_parts == 1
    assert node_pod6.outgoing_nodes[0].name == 'pod7'
    assert not node_pod6.hanging

    node_pod8 = graph.origin_nodes[node_names_list.index('pod8')]
    assert node_pod8.name == 'pod8'
    assert len(node_pod8.outgoing_nodes) == 1
    assert node_pod8.number_of_parts == 1
    assert node_pod8.outgoing_nodes[0].name == 'pod7'
    assert not node_pod8.hanging

    assert id(node_pod6.outgoing_nodes[0]) == id(node_pod8.outgoing_nodes[0])

    node_pod7 = node_pod6.outgoing_nodes[0]
    assert node_pod7.name == 'pod7'
    assert len(node_pod7.outgoing_nodes) == 1
    assert node_pod7.number_of_parts == 2
    assert node_pod7.outgoing_nodes[0].name == 'pod9'
    assert not node_pod7.hanging

    node_pod9 = node_pod7.outgoing_nodes[0]
    assert node_pod9.name == 'pod9'
    assert len(node_pod9.outgoing_nodes) == 0
    assert node_pod9.number_of_parts == 1
    assert node_pod9.hanging


def test_topology_graph_build_two_joins(two_joins_graph):
    graph = TopologyGraph(two_joins_graph)
    assert len(graph.origin_nodes) == 2
    origin_names = [node.name for node in graph.origin_nodes]
    assert set(origin_names) == {'p0', 'p1'}

    node_p0 = graph.origin_nodes[origin_names.index('p0')]
    assert node_p0.name == 'p0'
    assert node_p0.number_of_parts == 1
    assert len(node_p0.outgoing_nodes) == 1
    assert not node_p0.hanging

    node_p1 = graph.origin_nodes[origin_names.index('p1')]
    assert node_p1.name == 'p1'
    assert node_p1.number_of_parts == 1
    assert len(node_p1.outgoing_nodes) == 1
    assert not node_p1.hanging

    assert id(node_p0.outgoing_nodes[0]) == id(node_p1.outgoing_nodes[0])

    joiner_pod = node_p0.outgoing_nodes[0]
    assert joiner_pod.name == 'joiner_1'
    assert len(joiner_pod.outgoing_nodes) == 2
    assert joiner_pod.number_of_parts == 2
    assert not joiner_pod.hanging

    joiner_outgoing_list = [node.name for node in joiner_pod.outgoing_nodes]

    node_p2 = joiner_pod.outgoing_nodes[joiner_outgoing_list.index('p2')]
    assert node_p2.name == 'p2'
    assert len(node_p2.outgoing_nodes) == 1
    assert node_p2.number_of_parts == 1
    assert not node_p2.hanging

    node_p3 = joiner_pod.outgoing_nodes[joiner_outgoing_list.index('p3')]
    assert node_p3.name == 'p3'
    assert len(node_p3.outgoing_nodes) == 1
    assert node_p3.number_of_parts == 1
    assert not node_p3.hanging

    assert id(node_p2.outgoing_nodes[0]) == id(node_p3.outgoing_nodes[0])
    node_p4 = node_p2.outgoing_nodes[0]
    assert node_p4.name == 'p4'
    assert len(node_p4.outgoing_nodes) == 0
    assert node_p4.number_of_parts == 2
    assert not node_p4.hanging


class DummyMockConnectionPool:
    def __init__(self):
        self.sent_msg = defaultdict(dict)
        self.responded_messages = defaultdict(dict)

    def send_requests_once(
        self, requests: List[Request], pod: str, head: bool, endpoint: str = None
    ) -> asyncio.Task:
        assert head
        response_msg = copy.deepcopy(requests[0])
        new_docs = DocumentArray()
        for doc in requests[0].docs:
            clientid = doc.text[0:7]
            self.sent_msg[clientid][pod] = doc.text
            new_doc = Document(text=doc.text + f'-{clientid}-{pod}')
            new_docs.append(new_doc)
            self.responded_messages[clientid][pod] = new_doc.text

        response_msg.docs.clear()
        response_msg.docs.extend(new_docs)

        async def task_wrapper():
            import random

            await asyncio.sleep(1 / (random.randint(1, 3) * 10))
            return response_msg, {}

        return asyncio.create_task(task_wrapper())


class DummyMockGatewayRuntime:
    def __init__(self, graph_representation, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection_pool = DummyMockConnectionPool(*args, **kwargs)
        self.graph = TopologyGraph(graph_representation)

    async def receive_from_client(self, client_id, msg: 'Message'):
        graph = copy.deepcopy(self.graph)
        # important that the gateway needs to have an instance of the graph per request
        tasks_to_respond = []
        tasks_to_ignore = []
        for origin_node in graph.origin_nodes:
            leaf_tasks = origin_node.get_leaf_tasks(self.connection_pool, msg, None)
            # Every origin node returns a set of tasks that are the ones corresponding to the leafs of each of their subtrees that unwrap all the previous tasks.
            # It starts like a chain of waiting for tasks from previous nodes
            tasks_to_respond.extend([task for ret, task in leaf_tasks if ret])
            tasks_to_ignore.extend([task for ret, task in leaf_tasks if not ret])
        resp = await asyncio.gather(*tasks_to_respond)
        response, _ = zip(*resp)
        return client_id, response


def create_req_from_text(text: str):
    req = DataRequest()
    req.docs.append(Document(text=text))
    return req


@pytest.mark.asyncio
async def test_message_ordering_linear_graph(linear_graph_dict):
    runtime = DummyMockGatewayRuntime(linear_graph_dict)
    resps = await asyncio.gather(
        runtime.receive_from_client(0, create_req_from_text('client0-Request')),
        runtime.receive_from_client(1, create_req_from_text('client1-Request')),
        runtime.receive_from_client(2, create_req_from_text('client2-Request')),
        runtime.receive_from_client(3, create_req_from_text('client3-Request')),
        runtime.receive_from_client(4, create_req_from_text('client4-Request')),
        runtime.receive_from_client(5, create_req_from_text('client5-Request')),
        runtime.receive_from_client(6, create_req_from_text('client6-Request')),
        runtime.receive_from_client(7, create_req_from_text('client7-Request')),
        runtime.receive_from_client(8, create_req_from_text('client8-Request')),
        runtime.receive_from_client(9, create_req_from_text('client9-Request')),
    )
    assert len(resps) == 10
    for client_id, client_resps in resps:
        assert len(client_resps) == 1
        assert (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod1-client{client_id}-pod2-client{client_id}-pod3'
            == client_resps[0].docs[0].text
        )


@pytest.mark.asyncio
async def test_message_ordering_bifurcation_graph(bifurcation_graph_dict):
    runtime = DummyMockGatewayRuntime(bifurcation_graph_dict)
    resps = await asyncio.gather(
        runtime.receive_from_client(0, create_req_from_text('client0-Request')),
        runtime.receive_from_client(1, create_req_from_text('client1-Request')),
        runtime.receive_from_client(2, create_req_from_text('client2-Request')),
        runtime.receive_from_client(3, create_req_from_text('client3-Request')),
        runtime.receive_from_client(4, create_req_from_text('client4-Request')),
        runtime.receive_from_client(5, create_req_from_text('client5-Request')),
        runtime.receive_from_client(6, create_req_from_text('client6-Request')),
        runtime.receive_from_client(7, create_req_from_text('client7-Request')),
        runtime.receive_from_client(8, create_req_from_text('client8-Request')),
        runtime.receive_from_client(9, create_req_from_text('client9-Request')),
    )
    assert len(resps) == 10
    await asyncio.sleep(0.1)  # need to terminate the hanging pods tasks
    for client_id, client_resps in resps:
        assert len(client_resps) == 2
        sorted_clients_resps = list(
            sorted(client_resps, key=lambda msg: msg.docs[0].text)
        )

        assert (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod2-client{client_id}-pod3'
            == sorted_clients_resps[0].docs[0].text
        )
        assert (
            f'client{client_id}-Request-client{client_id}-pod4-client{client_id}-pod5'
            == sorted_clients_resps[1].docs[0].text
        )

        # assert the hanging pod was sent message
        assert (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod1'
            == runtime.connection_pool.responded_messages[f'client{client_id}']['pod1']
        )
        assert (
            f'client{client_id}-Request-client{client_id}-pod0'
            == runtime.connection_pool.sent_msg[f'client{client_id}']['pod1']
        )

        assert (
            f'client{client_id}-Request-client{client_id}-pod6'
            == runtime.connection_pool.responded_messages[f'client{client_id}']['pod6']
        )
        assert (
            f'client{client_id}-Request'
            == runtime.connection_pool.sent_msg[f'client{client_id}']['pod6']
        )


@pytest.mark.asyncio
async def test_message_ordering_merge_in_gateway_graph(
    merge_graph_dict_directly_merge_in_gateway,
):
    runtime = DummyMockGatewayRuntime(merge_graph_dict_directly_merge_in_gateway)
    resps = await asyncio.gather(
        runtime.receive_from_client(0, create_req_from_text('client0-Request')),
        runtime.receive_from_client(1, create_req_from_text('client1-Request')),
        runtime.receive_from_client(2, create_req_from_text('client2-Request')),
        runtime.receive_from_client(3, create_req_from_text('client3-Request')),
        runtime.receive_from_client(4, create_req_from_text('client4-Request')),
        runtime.receive_from_client(5, create_req_from_text('client5-Request')),
        runtime.receive_from_client(6, create_req_from_text('client6-Request')),
        runtime.receive_from_client(7, create_req_from_text('client7-Request')),
        runtime.receive_from_client(8, create_req_from_text('client8-Request')),
        runtime.receive_from_client(9, create_req_from_text('client9-Request')),
    )
    assert len(resps) == 10
    for client_id, client_resps in resps:
        assert len(client_resps) == 2
        assert (
            None in client_resps
        )  # at the merge branch, only responds to the last part
        filtered_client_resps = [resp for resp in client_resps if resp is not None]
        pod2_path = (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod2-client{client_id}-merger'
            in list(map(lambda resp: resp.data.docs[0].text, filtered_client_resps))
        )
        pod1_path = (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod1-client{client_id}-merger'
            in list(map(lambda resp: resp.data.docs[0].text, filtered_client_resps))
        )
        # TODO: need to add logic to merge messages
        assert pod1_path or pod2_path


@pytest.mark.asyncio
async def test_message_ordering_merge_in_last_pod_graph(
    merge_graph_dict_directly_merge_in_last_pod,
):
    runtime = DummyMockGatewayRuntime(merge_graph_dict_directly_merge_in_last_pod)
    resps = await asyncio.gather(
        runtime.receive_from_client(0, create_req_from_text('client0-Request')),
        runtime.receive_from_client(1, create_req_from_text('client1-Request')),
        runtime.receive_from_client(2, create_req_from_text('client2-Request')),
        runtime.receive_from_client(3, create_req_from_text('client3-Request')),
        runtime.receive_from_client(4, create_req_from_text('client4-Request')),
        runtime.receive_from_client(5, create_req_from_text('client5-Request')),
        runtime.receive_from_client(6, create_req_from_text('client6-Request')),
        runtime.receive_from_client(7, create_req_from_text('client7-Request')),
        runtime.receive_from_client(8, create_req_from_text('client8-Request')),
        runtime.receive_from_client(9, create_req_from_text('client9-Request')),
    )
    assert len(resps) == 10
    for client_id, client_resps in resps:
        assert len(client_resps) == 2
        assert (
            None in client_resps
        )  # at the merge branch, only responds to the last part
        filtered_client_resps = [resp for resp in client_resps if resp is not None]
        pod2_path = (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod2-client{client_id}-merger-client{client_id}-pod_last'
            in list(map(lambda resp: resp.data.docs[0].text, filtered_client_resps))
        )
        pod1_path = (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod1-client{client_id}-merger-client{client_id}-pod_last'
            in list(map(lambda resp: resp.data.docs[0].text, filtered_client_resps))
        )
        # TODO: need to add logic to merge messages
        assert pod1_path or pod2_path


@pytest.mark.asyncio
async def test_message_ordering_complete_graph(complete_graph_dict):
    runtime = DummyMockGatewayRuntime(complete_graph_dict)
    resps = await asyncio.gather(
        runtime.receive_from_client(0, create_req_from_text('client0-Request')),
        runtime.receive_from_client(1, create_req_from_text('client1-Request')),
        runtime.receive_from_client(2, create_req_from_text('client2-Request')),
        runtime.receive_from_client(3, create_req_from_text('client3-Request')),
        runtime.receive_from_client(4, create_req_from_text('client4-Request')),
        runtime.receive_from_client(5, create_req_from_text('client5-Request')),
        runtime.receive_from_client(6, create_req_from_text('client6-Request')),
        runtime.receive_from_client(7, create_req_from_text('client7-Request')),
        runtime.receive_from_client(8, create_req_from_text('client8-Request')),
        runtime.receive_from_client(9, create_req_from_text('client9-Request')),
    )
    assert len(resps) == 10
    await asyncio.sleep(0.1)  # need to terminate the hanging pods tasks
    for client_id, client_resps in resps:
        assert len(client_resps) == 3
        assert (
            None in client_resps
        )  # at the merge branch, only responds to the last part
        filtered_client_resps = [resp for resp in client_resps if resp is not None]
        assert len(filtered_client_resps) == 2
        sorted_filtered_client_resps = list(
            sorted(filtered_client_resps, key=lambda msg: msg.docs[0].text)
        )
        assert (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod1'
            == sorted_filtered_client_resps[0].docs[0].text
        )

        pod2_path = (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod2-client{client_id}-pod3-client{client_id}-merger-client{client_id}-pod_last'
            == sorted_filtered_client_resps[1].docs[0].text
        )
        pod4_path = (
            f'client{client_id}-Request-client{client_id}-pod4-client{client_id}-pod5-client{client_id}-merger-client{client_id}-pod_last'
            == sorted_filtered_client_resps[1].docs[0].text
        )

        assert pod2_path or pod4_path

        # assert the hanging pod was sent message
        assert (
            f'client{client_id}-Request-client{client_id}-pod6'
            == runtime.connection_pool.responded_messages[f'client{client_id}']['pod6']
        )
        assert (
            f'client{client_id}-Request'
            == runtime.connection_pool.sent_msg[f'client{client_id}']['pod6']
        )


@pytest.mark.asyncio
async def test_message_ordering_hanging_after_merge_graph(
    graph_hanging_pod_after_merge,
):
    runtime = DummyMockGatewayRuntime(graph_hanging_pod_after_merge)
    resps = await asyncio.gather(
        runtime.receive_from_client(0, create_req_from_text('client0-Request')),
        runtime.receive_from_client(1, create_req_from_text('client1-Request')),
        runtime.receive_from_client(2, create_req_from_text('client2-Request')),
        runtime.receive_from_client(3, create_req_from_text('client3-Request')),
        runtime.receive_from_client(4, create_req_from_text('client4-Request')),
        runtime.receive_from_client(5, create_req_from_text('client5-Request')),
        runtime.receive_from_client(6, create_req_from_text('client6-Request')),
        runtime.receive_from_client(7, create_req_from_text('client7-Request')),
        runtime.receive_from_client(8, create_req_from_text('client8-Request')),
        runtime.receive_from_client(9, create_req_from_text('client9-Request')),
    )
    assert len(resps) == 10
    await asyncio.sleep(0.1)  # need to terminate the hanging pods tasks
    for client_id, client_resps in resps:
        assert len(client_resps) == 2
        assert (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod2-client{client_id}-pod3'
            == client_resps[0].docs[0].text
        )
        assert (
            f'client{client_id}-Request-client{client_id}-pod4-client{client_id}-pod5'
            == client_resps[1].docs[0].text
        )

        # assert the hanging pod was sent message
        assert (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod1'
            == runtime.connection_pool.responded_messages[f'client{client_id}']['pod1']
        )
        assert (
            f'client{client_id}-Request-client{client_id}-pod0'
            == runtime.connection_pool.sent_msg[f'client{client_id}']['pod1']
        )

        path6 = (
            f'client{client_id}-Request-client{client_id}-pod6-client{client_id}-pod7-client{client_id}-pod9'
            == runtime.connection_pool.responded_messages[f'client{client_id}']['pod9']
        )
        path8 = (
            f'client{client_id}-Request-client{client_id}-pod8-client{client_id}-pod7-client{client_id}-pod9'
            == runtime.connection_pool.responded_messages[f'client{client_id}']['pod9']
        )
        assert path6 or path8

        if path6:
            assert (
                f'client{client_id}-Request-client{client_id}-pod6-client{client_id}-pod7'
                == runtime.connection_pool.sent_msg[f'client{client_id}']['pod9']
            )
        if path8:
            assert (
                f'client{client_id}-Request-client{client_id}-pod8-client{client_id}-pod7'
                == runtime.connection_pool.sent_msg[f'client{client_id}']['pod9']
            )


@pytest.mark.asyncio
async def test_message_ordering_two_joins_graph(
    two_joins_graph,
):
    runtime = DummyMockGatewayRuntime(two_joins_graph)
    resps = await asyncio.gather(
        runtime.receive_from_client(0, create_req_from_text('client0-Request')),
        runtime.receive_from_client(1, create_req_from_text('client1-Request')),
        runtime.receive_from_client(2, create_req_from_text('client2-Request')),
        runtime.receive_from_client(3, create_req_from_text('client3-Request')),
        runtime.receive_from_client(4, create_req_from_text('client4-Request')),
        runtime.receive_from_client(5, create_req_from_text('client5-Request')),
        runtime.receive_from_client(6, create_req_from_text('client6-Request')),
        runtime.receive_from_client(7, create_req_from_text('client7-Request')),
        runtime.receive_from_client(8, create_req_from_text('client8-Request')),
        runtime.receive_from_client(9, create_req_from_text('client9-Request')),
    )
    assert len(resps) == 10
    await asyncio.sleep(0.1)  # need to terminate the hanging pods tasks
    for client_id, client_resps in resps:
        assert len(client_resps) == 4
        filtered_client_resps = [resp for resp in client_resps if resp is not None]
        assert len(filtered_client_resps) == 1
        path12 = (
            f'client{client_id}-Request-client{client_id}-p1-client{client_id}-joiner_1-client{client_id}-p2-client{client_id}-p4'
            == filtered_client_resps[0].docs[0].text
        )
        path13 = (
            f'client{client_id}-Request-client{client_id}-p1-client{client_id}-joiner_1-client{client_id}-p3-client{client_id}-p4'
            == filtered_client_resps[0].docs[0].text
        )
        path02 = (
            f'client{client_id}-Request-client{client_id}-p0-client{client_id}-joiner_1-client{client_id}-p2-client{client_id}-p4'
            == filtered_client_resps[0].docs[0].text
        )
        path03 = (
            f'client{client_id}-Request-client{client_id}-p0-client{client_id}-joiner_1-client{client_id}-p3-client{client_id}-p4'
            == filtered_client_resps[0].docs[0].text
        )
        assert path02 or path03 or path12 or path13


def test_empty_graph():
    graph = TopologyGraph({})
    assert not graph.origin_nodes

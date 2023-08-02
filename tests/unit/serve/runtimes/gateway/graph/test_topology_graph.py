import asyncio
import copy
from collections import defaultdict
from typing import List

import pytest

from docarray import Document, DocumentArray
from jina.serve.runtimes.gateway.graph.topology_graph import TopologyGraph
from jina.types.request import Request
from jina.types.request.data import DataRequest


@pytest.fixture
def linear_graph_dict():
    return {
        'start-gateway': ['deployment0'],
        'deployment0': ['deployment1'],
        'deployment1': ['deployment2'],
        'deployment2': ['deployment3'],
        'deployment3': ['end-gateway'],
    }


@pytest.fixture
def bifurcation_graph_dict():
    return {
        'start-gateway': ['deployment0', 'deployment4', 'deployment6'],
        'deployment0': ['deployment1', 'deployment2'],
        'deployment1': [],  # hanging_deployment
        'deployment2': ['deployment3'],
        'deployment4': ['deployment5'],
        'deployment5': ['end-gateway'],
        'deployment3': ['end-gateway'],
        'deployment6': [],  # hanging_deployment
    }


@pytest.fixture
def merge_graph_dict_directly_merge_in_gateway():
    return {
        'start-gateway': ['deployment0'],
        'deployment0': ['deployment1', 'deployment2'],
        'deployment1': ['merger'],
        'deployment2': ['merger'],
        'merger': ['end-gateway'],
    }


@pytest.fixture
def merge_graph_dict_directly_merge_in_last_deployment():
    return {
        'start-gateway': ['deployment0'],
        'deployment0': ['deployment1', 'deployment2'],
        'deployment1': ['merger'],
        'deployment2': ['merger'],
        'merger': ['deployment_last'],
        'deployment_last': ['end-gateway'],
    }


@pytest.fixture
def complete_graph_dict():
    return {
        'start-gateway': ['deployment0', 'deployment4', 'deployment6'],
        'deployment0': ['deployment1', 'deployment2'],
        'deployment1': ['end-gateway'],
        'deployment2': ['deployment3'],
        'deployment4': ['deployment5'],
        'merger': ['deployment_last'],
        'deployment5': ['merger'],
        'deployment3': ['merger'],
        'deployment6': [],  # hanging_deployment
        'deployment_last': ['end-gateway'],
    }


@pytest.fixture
def graph_hanging_deployment_after_merge():
    return {
        'start-gateway': ['deployment0', 'deployment4', 'deployment6', 'deployment8'],
        'deployment0': ['deployment1', 'deployment2'],
        'deployment1': [],  # hanging_deployment
        'deployment2': ['deployment3'],
        'deployment4': ['deployment5'],
        'deployment5': ['end-gateway'],
        'deployment3': ['end-gateway'],
        'deployment6': ['deployment7'],
        'deployment8': ['deployment7'],
        'deployment7': ['deployment9'],
        'deployment9': [],  # hanging_deployment
    }


@pytest.fixture
def two_joins_graph():
    return {
        'start-gateway': ['p0', 'p1'],
        'p0': ['joiner_1'],
        'p1': ['joiner_1'],  # hanging_deployment
        'joiner_1': ['p2', 'p3'],
        'p2': ['p4'],
        'p3': ['p4'],
        'p4': ['end-gateway'],
    }


def test_topology_graph_build_linear(linear_graph_dict):
    graph = TopologyGraph(linear_graph_dict)
    assert [node.name for node in graph.origin_nodes] == ['deployment0']
    node_deployment0 = graph.origin_nodes[0]
    assert node_deployment0.name == 'deployment0'
    assert node_deployment0.number_of_parts == 1
    assert len(node_deployment0.outgoing_nodes) == 1
    assert not node_deployment0.floating

    node_deployment1 = node_deployment0.outgoing_nodes[0]
    assert node_deployment1.name == 'deployment1'
    assert node_deployment1.number_of_parts == 1
    assert len(node_deployment1.outgoing_nodes) == 1
    assert not node_deployment1.floating

    node_deployment2 = node_deployment1.outgoing_nodes[0]
    assert node_deployment2.name == 'deployment2'
    assert node_deployment2.number_of_parts == 1
    assert len(node_deployment2.outgoing_nodes) == 1
    assert not node_deployment2.floating

    node_deployment3 = node_deployment2.outgoing_nodes[0]
    assert node_deployment3.name == 'deployment3'
    assert node_deployment3.number_of_parts == 1
    assert len(node_deployment3.outgoing_nodes) == 1
    assert node_deployment3.outgoing_nodes[0].name == '__end_gateway__'
    assert not node_deployment3.floating


@pytest.mark.parametrize(
    'conditions',
    [
        {},
        {
            'deployment1': {'tags__key': {'$eq': 5}},
            'deployment2': {'tags__key': {'$eq': 4}},
        },
    ],
)
def test_topology_graph_build_bifurcation(bifurcation_graph_dict, conditions):
    graph = TopologyGraph(bifurcation_graph_dict, conditions)
    node_names_list = [node.name for node in graph.origin_nodes]
    assert set(node_names_list) == {'deployment0', 'deployment4', 'deployment6'}
    assert (
        len(graph.origin_nodes[node_names_list.index('deployment0')].outgoing_nodes)
        == 2
    )
    assert set(
        [
            node.name
            for node in graph.origin_nodes[
                node_names_list.index('deployment0')
            ].outgoing_nodes
        ]
    ) == {'deployment1', 'deployment2'}

    node_deployment0 = graph.origin_nodes[node_names_list.index('deployment0')]
    assert not node_deployment0.floating
    assert node_deployment0.name == 'deployment0'
    assert node_deployment0.number_of_parts == 1
    outgoing_deployment0_list = [node.name for node in node_deployment0.outgoing_nodes]

    node_deployment1 = node_deployment0.outgoing_nodes[
        outgoing_deployment0_list.index('deployment1')
    ]
    assert node_deployment1.name == 'deployment1'
    if conditions == {}:
        assert node_deployment1._filter_condition is None
    else:
        assert node_deployment1._filter_condition == {'tags__key': {'$eq': 5}}
    assert node_deployment1.number_of_parts == 1
    assert len(node_deployment1.outgoing_nodes) == 0
    assert node_deployment1.floating

    node_deployment2 = node_deployment0.outgoing_nodes[
        outgoing_deployment0_list.index('deployment2')
    ]
    assert node_deployment2.name == 'deployment2'
    if conditions == {}:
        assert node_deployment2._filter_condition is None
    else:
        assert node_deployment2._filter_condition == {'tags__key': {'$eq': 4}}
    assert node_deployment2.number_of_parts == 1
    assert len(node_deployment2.outgoing_nodes) == 1
    assert not node_deployment2.floating

    node_deployment3 = node_deployment2.outgoing_nodes[0]
    assert node_deployment3.name == 'deployment3'
    assert node_deployment3.number_of_parts == 1
    assert len(node_deployment3.outgoing_nodes) == 1
    assert node_deployment3.outgoing_nodes[0].name == '__end_gateway__'
    assert not node_deployment3.floating

    node_deployment4 = graph.origin_nodes[node_names_list.index('deployment4')]
    assert node_deployment4.name == 'deployment4'
    assert node_deployment4.number_of_parts == 1
    assert len(node_deployment4.outgoing_nodes) == 1
    assert not node_deployment4.floating
    assert set(
        [
            node.name
            for node in graph.origin_nodes[
                node_names_list.index('deployment4')
            ].outgoing_nodes
        ]
    ) == {'deployment5'}

    node_deployment5 = node_deployment4.outgoing_nodes[0]
    assert node_deployment5.name == 'deployment5'
    assert node_deployment5.number_of_parts == 1
    assert not node_deployment5.floating
    assert len(node_deployment5.outgoing_nodes) == 1
    assert node_deployment5.outgoing_nodes[0].name == '__end_gateway__'

    node_deployment6 = graph.origin_nodes[node_names_list.index('deployment6')]
    assert node_deployment6.name == 'deployment6'
    assert len(node_deployment6.outgoing_nodes) == 0
    assert node_deployment6.number_of_parts == 1
    assert node_deployment6.floating
    assert set([node.name for node in node_deployment6.outgoing_nodes]) == set()


def test_topology_graph_build_merge_in_gateway(
    merge_graph_dict_directly_merge_in_gateway,
):
    graph = TopologyGraph(merge_graph_dict_directly_merge_in_gateway)
    assert set([node.name for node in graph.origin_nodes]) == {'deployment0'}

    node_deployment0 = graph.origin_nodes[0]
    assert node_deployment0.name == 'deployment0'
    assert not node_deployment0.floating
    assert len(node_deployment0.outgoing_nodes) == 2
    outgoing_deployment0_list = [node.name for node in node_deployment0.outgoing_nodes]
    assert node_deployment0.number_of_parts == 1

    node_deployment1 = node_deployment0.outgoing_nodes[
        outgoing_deployment0_list.index('deployment1')
    ]
    assert node_deployment1.name == 'deployment1'
    assert len(node_deployment1.outgoing_nodes) == 1
    assert node_deployment1.outgoing_nodes[0].name == 'merger'
    assert node_deployment1.number_of_parts == 1
    assert not node_deployment1.floating

    node_deployment2 = node_deployment0.outgoing_nodes[
        outgoing_deployment0_list.index('deployment2')
    ]
    assert node_deployment2.name == 'deployment2'
    assert len(node_deployment2.outgoing_nodes) == 1
    assert node_deployment2.outgoing_nodes[0].name == 'merger'
    assert node_deployment2.number_of_parts == 1
    assert not node_deployment2.floating
    assert id(node_deployment1.outgoing_nodes[0]) == id(
        node_deployment2.outgoing_nodes[0]
    )

    merger_deployment = node_deployment1.outgoing_nodes[0]
    assert merger_deployment.name == 'merger'
    assert merger_deployment.number_of_parts == 2
    assert len(merger_deployment.outgoing_nodes) == 1
    assert merger_deployment.outgoing_nodes[0].name == '__end_gateway__'
    assert not merger_deployment.floating


def test_topology_graph_build_merge_in_last_deployment(
    merge_graph_dict_directly_merge_in_last_deployment,
):
    graph = TopologyGraph(merge_graph_dict_directly_merge_in_last_deployment)
    assert set([node.name for node in graph.origin_nodes]) == {'deployment0'}

    node_deployment0 = graph.origin_nodes[0]
    assert node_deployment0.number_of_parts == 1
    assert len(node_deployment0.outgoing_nodes) == 2
    assert not node_deployment0.floating
    outgoing_deployment0_list = [node.name for node in node_deployment0.outgoing_nodes]

    node_deployment1 = node_deployment0.outgoing_nodes[
        outgoing_deployment0_list.index('deployment1')
    ]
    assert node_deployment1.number_of_parts == 1
    assert len(node_deployment1.outgoing_nodes) == 1
    assert node_deployment1.outgoing_nodes[0].name == 'merger'
    assert not node_deployment1.floating

    node_deployment2 = node_deployment0.outgoing_nodes[
        outgoing_deployment0_list.index('deployment2')
    ]
    assert node_deployment2.number_of_parts == 1
    assert len(node_deployment2.outgoing_nodes) == 1
    assert node_deployment2.outgoing_nodes[0].name == 'merger'
    assert not node_deployment2.floating

    assert id(node_deployment1.outgoing_nodes[0]) == id(
        node_deployment2.outgoing_nodes[0]
    )

    merger_deployment = node_deployment1.outgoing_nodes[0]
    assert merger_deployment.name == 'merger'
    assert len(merger_deployment.outgoing_nodes) == 1
    assert merger_deployment.number_of_parts == 2
    assert not merger_deployment.floating

    deployment_last_deployment = merger_deployment.outgoing_nodes[0]
    assert deployment_last_deployment.name == 'deployment_last'
    assert len(deployment_last_deployment.outgoing_nodes) == 1
    assert deployment_last_deployment.outgoing_nodes[0].name == '__end_gateway__'
    assert deployment_last_deployment.number_of_parts == 1
    assert not deployment_last_deployment.floating


def test_topology_graph_build_complete(complete_graph_dict):
    graph = TopologyGraph(complete_graph_dict)
    assert set([node.name for node in graph.origin_nodes]) == {
        'deployment0',
        'deployment4',
        'deployment6',
    }
    node_names_list = [node.name for node in graph.origin_nodes]

    node_deployment0 = graph.origin_nodes[node_names_list.index('deployment0')]
    assert node_deployment0.number_of_parts == 1
    assert not node_deployment0.floating
    outgoing_deployment0_list = [node.name for node in node_deployment0.outgoing_nodes]

    node_deployment1 = node_deployment0.outgoing_nodes[
        outgoing_deployment0_list.index('deployment1')
    ]
    assert node_deployment1.number_of_parts == 1
    assert not node_deployment1.floating
    assert len(node_deployment1.outgoing_nodes) == 1
    assert node_deployment1.outgoing_nodes[0].name == '__end_gateway__'

    node_deployment2 = node_deployment0.outgoing_nodes[
        outgoing_deployment0_list.index('deployment2')
    ]
    assert len(node_deployment2.outgoing_nodes) == 1
    assert node_deployment2.number_of_parts == 1
    assert not node_deployment2.floating

    node_deployment3 = node_deployment2.outgoing_nodes[0]
    assert node_deployment3.name == 'deployment3'
    assert node_deployment3.number_of_parts == 1
    assert len(node_deployment3.outgoing_nodes) == 1
    assert node_deployment3.outgoing_nodes[0].name == 'merger'
    assert not node_deployment3.floating

    node_deployment4 = graph.origin_nodes[node_names_list.index('deployment4')]
    assert node_deployment4.number_of_parts == 1
    assert len(node_deployment4.outgoing_nodes) == 1
    assert not node_deployment4.floating

    node_deployment5 = node_deployment4.outgoing_nodes[0]
    assert node_deployment5.number_of_parts == 1
    assert node_deployment5.name == 'deployment5'
    assert len(node_deployment5.outgoing_nodes) == 1
    assert node_deployment5.outgoing_nodes[0].name == 'merger'
    assert not node_deployment5.floating

    assert id(node_deployment3.outgoing_nodes[0]) == id(
        node_deployment5.outgoing_nodes[0]
    )

    merger_deployment = node_deployment3.outgoing_nodes[0]
    assert merger_deployment.name == 'merger'
    assert len(merger_deployment.outgoing_nodes) == 1
    assert merger_deployment.number_of_parts == 2
    assert not merger_deployment.floating

    deployment_last_deployment = merger_deployment.outgoing_nodes[0]
    assert deployment_last_deployment.name == 'deployment_last'
    assert len(deployment_last_deployment.outgoing_nodes) == 1
    assert deployment_last_deployment.outgoing_nodes[0].name == '__end_gateway__'
    assert deployment_last_deployment.number_of_parts == 1
    assert not deployment_last_deployment.floating

    node_deployment6 = graph.origin_nodes[node_names_list.index('deployment6')]
    assert node_deployment6.name == 'deployment6'
    assert node_deployment6.number_of_parts == 1
    assert len(node_deployment6.outgoing_nodes) == 0
    assert node_deployment6.floating


def test_topology_graph_build_hanging_after_merge(graph_hanging_deployment_after_merge):
    graph = TopologyGraph(graph_hanging_deployment_after_merge)
    node_names_list = [node.name for node in graph.origin_nodes]
    assert set(node_names_list) == {
        'deployment0',
        'deployment4',
        'deployment6',
        'deployment8',
    }
    assert (
        len(graph.origin_nodes[node_names_list.index('deployment0')].outgoing_nodes)
        == 2
    )
    assert set(
        [
            node.name
            for node in graph.origin_nodes[
                node_names_list.index('deployment0')
            ].outgoing_nodes
        ]
    ) == {'deployment1', 'deployment2'}

    node_deployment0 = graph.origin_nodes[node_names_list.index('deployment0')]
    assert node_deployment0.name == 'deployment0'
    assert node_deployment0.number_of_parts == 1
    assert not node_deployment0.floating
    outgoing_deployment0_list = [node.name for node in node_deployment0.outgoing_nodes]

    node_deployment1 = node_deployment0.outgoing_nodes[
        outgoing_deployment0_list.index('deployment1')
    ]
    assert node_deployment1.name == 'deployment1'
    assert node_deployment1.number_of_parts == 1
    assert len(node_deployment1.outgoing_nodes) == 0
    assert node_deployment1.floating

    node_deployment2 = node_deployment0.outgoing_nodes[
        outgoing_deployment0_list.index('deployment2')
    ]
    assert node_deployment2.name == 'deployment2'
    assert node_deployment2.number_of_parts == 1
    assert len(node_deployment2.outgoing_nodes) == 1
    assert not node_deployment2.floating

    node_deployment3 = node_deployment2.outgoing_nodes[0]
    assert node_deployment3.name == 'deployment3'
    assert node_deployment3.number_of_parts == 1
    assert len(node_deployment3.outgoing_nodes) == 1
    assert node_deployment3.outgoing_nodes[0].name == '__end_gateway__'
    assert not node_deployment3.floating

    node_deployment4 = graph.origin_nodes[node_names_list.index('deployment4')]
    assert node_deployment4.name == 'deployment4'
    assert node_deployment4.number_of_parts == 1
    assert len(node_deployment4.outgoing_nodes) == 1
    assert set(
        [
            node.name
            for node in graph.origin_nodes[
                node_names_list.index('deployment4')
            ].outgoing_nodes
        ]
    ) == {'deployment5'}
    assert not node_deployment4.floating

    node_deployment5 = node_deployment4.outgoing_nodes[0]
    assert node_deployment5.name == 'deployment5'
    assert node_deployment5.number_of_parts == 1
    assert len(node_deployment5.outgoing_nodes) == 1
    assert node_deployment5.outgoing_nodes[0].name == '__end_gateway__'
    assert not node_deployment5.floating

    node_deployment6 = graph.origin_nodes[node_names_list.index('deployment6')]
    assert node_deployment6.name == 'deployment6'
    assert len(node_deployment6.outgoing_nodes) == 1
    assert node_deployment6.number_of_parts == 1
    assert node_deployment6.outgoing_nodes[0].name == 'deployment7'
    assert not node_deployment6.floating

    node_deployment8 = graph.origin_nodes[node_names_list.index('deployment8')]
    assert node_deployment8.name == 'deployment8'
    assert len(node_deployment8.outgoing_nodes) == 1
    assert node_deployment8.number_of_parts == 1
    assert node_deployment8.outgoing_nodes[0].name == 'deployment7'
    assert not node_deployment8.floating

    assert id(node_deployment6.outgoing_nodes[0]) == id(
        node_deployment8.outgoing_nodes[0]
    )

    node_deployment7 = node_deployment6.outgoing_nodes[0]
    assert node_deployment7.name == 'deployment7'
    assert len(node_deployment7.outgoing_nodes) == 1
    assert node_deployment7.number_of_parts == 2
    assert node_deployment7.outgoing_nodes[0].name == 'deployment9'
    assert not node_deployment7.floating

    node_deployment9 = node_deployment7.outgoing_nodes[0]
    assert node_deployment9.name == 'deployment9'
    assert len(node_deployment9.outgoing_nodes) == 0
    assert node_deployment9.number_of_parts == 1
    assert node_deployment9.floating


def test_topology_graph_build_two_joins(two_joins_graph):
    graph = TopologyGraph(two_joins_graph)
    assert len(graph.origin_nodes) == 2
    origin_names = [node.name for node in graph.origin_nodes]
    assert set(origin_names) == {'p0', 'p1'}

    node_p0 = graph.origin_nodes[origin_names.index('p0')]
    assert node_p0.name == 'p0'
    assert node_p0.number_of_parts == 1
    assert len(node_p0.outgoing_nodes) == 1
    assert not node_p0.floating

    node_p1 = graph.origin_nodes[origin_names.index('p1')]
    assert node_p1.name == 'p1'
    assert node_p1.number_of_parts == 1
    assert len(node_p1.outgoing_nodes) == 1
    assert not node_p1.floating

    assert id(node_p0.outgoing_nodes[0]) == id(node_p1.outgoing_nodes[0])

    joiner_deployment = node_p0.outgoing_nodes[0]
    assert joiner_deployment.name == 'joiner_1'
    assert len(joiner_deployment.outgoing_nodes) == 2
    assert joiner_deployment.number_of_parts == 2
    assert not joiner_deployment.floating

    joiner_outgoing_list = [node.name for node in joiner_deployment.outgoing_nodes]

    node_p2 = joiner_deployment.outgoing_nodes[joiner_outgoing_list.index('p2')]
    assert node_p2.name == 'p2'
    assert len(node_p2.outgoing_nodes) == 1
    assert node_p2.number_of_parts == 1
    assert not node_p2.floating

    node_p3 = joiner_deployment.outgoing_nodes[joiner_outgoing_list.index('p3')]
    assert node_p3.name == 'p3'
    assert len(node_p3.outgoing_nodes) == 1
    assert node_p3.number_of_parts == 1
    assert not node_p3.floating

    assert id(node_p2.outgoing_nodes[0]) == id(node_p3.outgoing_nodes[0])
    node_p4 = node_p2.outgoing_nodes[0]
    assert node_p4.name == 'p4'
    assert len(node_p4.outgoing_nodes) == 1
    assert node_p4.outgoing_nodes[0].name == '__end_gateway__'
    assert node_p4.number_of_parts == 2
    assert not node_p4.floating


class DummyMockConnectionPool:
    def __init__(self):
        self.sent_msg = defaultdict(dict)
        self.responded_messages = defaultdict(dict)
        self.deployments_called = []

    def send_requests_once(
        self,
        requests: List[Request],
        deployment: str,
        head: bool,
        metadata: dict = None,
        endpoint: str = None,
        timeout: float = 1.0,
        retries: int = -1,
    ) -> asyncio.Task:
        assert head
        self.deployments_called.append(deployment)
        response_msg = copy.deepcopy(requests[0])
        new_docs = DocumentArray()
        for doc in requests[0].docs:
            clientid = doc.text[0:7]
            self.sent_msg[clientid][deployment] = doc.text
            new_doc = Document(
                text=doc.text + f'-{clientid}-{deployment}', tags=doc.tags
            )
            new_docs.append(new_doc)
            self.responded_messages[clientid][deployment] = new_doc.text

        response_msg.data.docs = new_docs

        async def task_wrapper():
            import random

            await asyncio.sleep(1 / (random.randint(1, 3) * 10))
            return response_msg, {}

        return asyncio.create_task(task_wrapper())


class DummyMockGatewayRuntime:
    def __init__(
        self,
        graph_representation,
        conditions={},
        deployments_metadata={},
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.connection_pool = DummyMockConnectionPool(*args, **kwargs)
        self.graph = TopologyGraph(
            graph_representation,
            graph_conditions=conditions,
            deployments_metadata=deployments_metadata,
        )

    async def receive_from_client(self, client_id, msg: 'DataRequest'):
        graph = copy.deepcopy(self.graph)
        # important that the gateway needs to have an instance of the graph per request
        tasks_to_respond = []
        tasks_to_ignore = []
        for origin_node in graph.origin_nodes:
            leaf_tasks = origin_node.get_leaf_req_response_tasks(self.connection_pool, msg, None)
            # Every origin node returns a set of tasks that are the ones corresponding to the leafs of each of their subtrees that unwrap all the previous tasks.
            # It starts like a chain of waiting for tasks from previous nodes
            tasks_to_respond.extend([task for ret, task in leaf_tasks if ret])
            tasks_to_ignore.extend([task for ret, task in leaf_tasks if not ret])
        resp = await asyncio.gather(*tasks_to_respond)
        response, _ = zip(*resp)
        return client_id, response


def create_req_from_text(text: str):
    req = DataRequest()
    da = DocumentArray()
    da.append(Document(text=text, tags={'key': 4}))
    req.data.docs = da
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
            f'client{client_id}-Request-client{client_id}-deployment0-client{client_id}-deployment1-client{client_id}-deployment2-client{client_id}-deployment3'
            == client_resps[0].docs[0].text
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'conditions, node_skipped',
    [
        ({}, ''),
        (
            {
                'deployment1': {'tags__key': {'$eq': 5}},
                'deployment2': {'tags__key': {'$eq': 4}},
            },
            'deployment1',
        ),
        (
            {
                'deployment1': {'tags__key': {'$eq': 4}},
                'deployment2': {'tags__key': {'$eq': 5}},
            },
            'deployment2',
        ),
    ],
)
async def test_message_ordering_bifurcation_graph(
    bifurcation_graph_dict, conditions, node_skipped
):
    runtime = DummyMockGatewayRuntime(bifurcation_graph_dict, conditions)
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
    await asyncio.sleep(0.1)  # need to terminate the floating deployments tasks
    for client_id, client_resps in resps:
        assert len(client_resps) == 2

        def sorting_key(msg):
            if len(msg.docs) > 0:
                return msg.docs[0].text
            else:
                return '-1'

        sorted_clients_resps = list(sorted(client_resps, key=sorting_key))

        if node_skipped != 'deployment2':
            assert (
                f'client{client_id}-Request-client{client_id}-deployment0-client{client_id}-deployment2-client{client_id}-deployment3'
                == sorted_clients_resps[0].docs[0].text
            )
        else:
            assert len(sorted_clients_resps[0].docs) == 0

        assert (
            f'client{client_id}-Request-client{client_id}-deployment4-client{client_id}-deployment5'
            == sorted_clients_resps[1].docs[0].text
        )

        # assert the floating deployment was sent message
        if node_skipped != 'deployment1':
            assert (
                f'client{client_id}-Request-client{client_id}-deployment0-client{client_id}-deployment1'
                == runtime.connection_pool.responded_messages[f'client{client_id}'][
                    'deployment1'
                ]
            )
            assert (
                f'client{client_id}-Request-client{client_id}-deployment0'
                == runtime.connection_pool.sent_msg[f'client{client_id}']['deployment1']
            )
        else:
            assert (
                'deployment1'
                not in runtime.connection_pool.sent_msg[f'client{client_id}']
            )

        assert (
            f'client{client_id}-Request-client{client_id}-deployment6'
            == runtime.connection_pool.responded_messages[f'client{client_id}'][
                'deployment6'
            ]
        )
        assert (
            f'client{client_id}-Request'
            == runtime.connection_pool.sent_msg[f'client{client_id}']['deployment6']
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
        deployment2_path = (
            f'client{client_id}-Request-client{client_id}-deployment0-client{client_id}-deployment2-client{client_id}-merger'
            in list(map(lambda resp: resp.data.docs[0].text, filtered_client_resps))
        )
        deployment1_path = (
            f'client{client_id}-Request-client{client_id}-deployment0-client{client_id}-deployment1-client{client_id}-merger'
            in list(map(lambda resp: resp.data.docs[0].text, filtered_client_resps))
        )
        # TODO: need to add logic to merge messages
        assert deployment1_path or deployment2_path


@pytest.mark.asyncio
async def test_message_ordering_merge_in_last_deployment_graph(
    merge_graph_dict_directly_merge_in_last_deployment,
):
    runtime = DummyMockGatewayRuntime(
        merge_graph_dict_directly_merge_in_last_deployment
    )
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
        deployment2_path = (
            f'client{client_id}-Request-client{client_id}-deployment0-client{client_id}-deployment2-client{client_id}-merger-client{client_id}-deployment_last'
            in list(map(lambda resp: resp.data.docs[0].text, filtered_client_resps))
        )
        deployment1_path = (
            f'client{client_id}-Request-client{client_id}-deployment0-client{client_id}-deployment1-client{client_id}-merger-client{client_id}-deployment_last'
            in list(map(lambda resp: resp.data.docs[0].text, filtered_client_resps))
        )
        # TODO: need to add logic to merge messages
        assert deployment1_path or deployment2_path


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
    await asyncio.sleep(0.1)  # need to terminate the floating deployments tasks
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
            f'client{client_id}-Request-client{client_id}-deployment0-client{client_id}-deployment1'
            == sorted_filtered_client_resps[0].docs[0].text
        )

        deployment2_path = (
            f'client{client_id}-Request-client{client_id}-deployment0-client{client_id}-deployment2-client{client_id}-deployment3-client{client_id}-merger-client{client_id}-deployment_last'
            == sorted_filtered_client_resps[1].docs[0].text
        )
        deployment4_path = (
            f'client{client_id}-Request-client{client_id}-deployment4-client{client_id}-deployment5-client{client_id}-merger-client{client_id}-deployment_last'
            == sorted_filtered_client_resps[1].docs[0].text
        )

        assert deployment2_path or deployment4_path

        # assert the floating deployment was sent message
        assert (
            f'client{client_id}-Request-client{client_id}-deployment6'
            == runtime.connection_pool.responded_messages[f'client{client_id}'][
                'deployment6'
            ]
        )
        assert (
            f'client{client_id}-Request'
            == runtime.connection_pool.sent_msg[f'client{client_id}']['deployment6']
        )


@pytest.mark.asyncio
async def test_message_ordering_hanging_after_merge_graph(
    graph_hanging_deployment_after_merge,
):
    runtime = DummyMockGatewayRuntime(graph_hanging_deployment_after_merge)
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
    await asyncio.sleep(0.1)  # need to terminate the floating deployments tasks
    for client_id, client_resps in resps:
        assert len(client_resps) == 2
        assert (
            f'client{client_id}-Request-client{client_id}-deployment0-client{client_id}-deployment2-client{client_id}-deployment3'
            == client_resps[0].docs[0].text
        )
        assert (
            f'client{client_id}-Request-client{client_id}-deployment4-client{client_id}-deployment5'
            == client_resps[1].docs[0].text
        )

        # assert the floating deployment was sent message
        assert (
            f'client{client_id}-Request-client{client_id}-deployment0-client{client_id}-deployment1'
            == runtime.connection_pool.responded_messages[f'client{client_id}'][
                'deployment1'
            ]
        )
        assert (
            f'client{client_id}-Request-client{client_id}-deployment0'
            == runtime.connection_pool.sent_msg[f'client{client_id}']['deployment1']
        )

        path6 = (
            f'client{client_id}-Request-client{client_id}-deployment6-client{client_id}-deployment7-client{client_id}-deployment9'
            == runtime.connection_pool.responded_messages[f'client{client_id}'][
                'deployment9'
            ]
        )
        path8 = (
            f'client{client_id}-Request-client{client_id}-deployment8-client{client_id}-deployment7-client{client_id}-deployment9'
            == runtime.connection_pool.responded_messages[f'client{client_id}'][
                'deployment9'
            ]
        )
        assert path6 or path8

        if path6:
            assert (
                f'client{client_id}-Request-client{client_id}-deployment6-client{client_id}-deployment7'
                == runtime.connection_pool.sent_msg[f'client{client_id}']['deployment9']
            )
        if path8:
            assert (
                f'client{client_id}-Request-client{client_id}-deployment8-client{client_id}-deployment7'
                == runtime.connection_pool.sent_msg[f'client{client_id}']['deployment9']
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
    await asyncio.sleep(0.1)  # need to terminate the floating deployments tasks
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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'deployments_metadata',
    [
        ({}),
        (
            {
                'deployment1': {'key1': 'value1'},
                'deployment2': {'key2': 'value2'},
            }
        ),
    ],
)
async def test_deployment_metadata_in_graph(linear_graph_dict, deployments_metadata):
    runtime = DummyMockGatewayRuntime(
        linear_graph_dict, deployments_metadata=deployments_metadata
    )
    for node in runtime.graph.origin_nodes:
        if node.name in deployments_metadata:
            assert node._metadata == deployments_metadata[node.name]

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
            f'client{client_id}-Request-client{client_id}-deployment0-client{client_id}-deployment1-client{client_id}-deployment2-client{client_id}-deployment3'
            == client_resps[0].docs[0].text
        )


def test_empty_graph():
    graph = TopologyGraph({})
    assert not graph.origin_nodes

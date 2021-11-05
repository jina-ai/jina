import copy
import pytest
import asyncio

from jina.peapods.runtimes.gateway.graph.topology_graph import TopologyGraph


@pytest.fixture
def linear_graph_dict():
    return {'pod0': ['pod1'], 'pod1': ['pod2'], 'pod2': ['pod3']}


@pytest.fixture
def bifurcation_graph_dict():
    return {
        'pod0': ['pod1', 'pod2'],
        'pod1': [],
        'pod2': ['pod3'],
        'pod4': ['pod5'],
        'pod5': [],
        'pod3': [],
        'pod6': [],
    }


@pytest.fixture
def merge_graph_dict_directly_merge_in_gateway():
    return {
        'pod0': ['pod1', 'pod2'],
        'pod1': ['merger'],
        'pod2': ['merger'],
        'merger': [],
    }


@pytest.fixture
def merge_graph_dict_directly_merge_in_last_pod():
    return {
        'pod0': ['pod1', 'pod2'],
        'pod1': ['merger'],
        'pod2': ['merger'],
        'merger': ['pod_last'],
        'pod_last': [],
    }


@pytest.fixture
def complete_graph_dict():
    return {
        'pod0': ['pod1', 'pod2'],
        'pod1': [],
        'pod2': ['pod3'],
        'pod4': ['pod5'],
        'merger': ['pod_last'],
        'pod5': ['merger'],
        'pod3': ['merger'],
        'pod6': [],
        'pod_last': [],
    }


def test_topology_graph_build_linear(linear_graph_dict):
    graph = TopologyGraph(linear_graph_dict)
    assert [node.name for node in graph.origin_nodes] == ['pod0']
    assert graph.origin_nodes[0].name == 'pod0'
    assert graph.origin_nodes[0].number_of_parts == 1
    assert graph.origin_nodes[0].outgoing_nodes[0].name == 'pod1'
    assert graph.origin_nodes[0].outgoing_nodes[0].number_of_parts == 1
    assert graph.origin_nodes[0].outgoing_nodes[0].outgoing_nodes[0].name == 'pod2'
    assert (
        graph.origin_nodes[0].outgoing_nodes[0].outgoing_nodes[0].number_of_parts == 1
    )
    assert (
        graph.origin_nodes[0].outgoing_nodes[0].outgoing_nodes[0].outgoing_nodes[0].name
        == 'pod3'
    )
    assert (
        graph.origin_nodes[0]
        .outgoing_nodes[0]
        .outgoing_nodes[0]
        .outgoing_nodes[0]
        .number_of_parts
        == 1
    )
    assert (
        len(
            graph.origin_nodes[0]
            .outgoing_nodes[0]
            .outgoing_nodes[0]
            .outgoing_nodes[0]
            .outgoing_nodes
        )
        == 0
    )


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
    assert node_pod0.name == 'pod0'
    assert node_pod0.number_of_parts == 1
    outgoing_pod0_list = [node.name for node in node_pod0.outgoing_nodes]

    node_pod1 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod1')]
    assert node_pod1.name == 'pod1'
    assert node_pod1.number_of_parts == 1
    assert len(node_pod1.outgoing_nodes) == 0
    node_pod2 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod2')]
    assert node_pod2.name == 'pod2'
    assert node_pod2.number_of_parts == 1
    assert len(node_pod2.outgoing_nodes) == 1

    node_pod3 = node_pod2.outgoing_nodes[0]
    assert node_pod3.name == 'pod3'
    assert node_pod3.number_of_parts == 1
    assert len(node_pod3.outgoing_nodes) == 0

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

    node_pod4 = graph.origin_nodes[node_names_list.index('pod4')]
    assert node_pod4.number_of_parts == 1
    node_pod5 = node_pod4.outgoing_nodes[0]
    assert node_pod5.name == 'pod5'
    assert node_pod5.number_of_parts == 1
    assert len(node_pod5.outgoing_nodes) == 0

    node_pod6 = graph.origin_nodes[node_names_list.index('pod6')]
    assert node_pod6.name == 'pod6'
    assert len(node_pod6.outgoing_nodes) == 0
    assert node_pod6.number_of_parts == 1
    assert set([node.name for node in node_pod6.outgoing_nodes]) == set()


def test_topology_graph_build_merge_in_gateway(
    merge_graph_dict_directly_merge_in_gateway,
):
    graph = TopologyGraph(merge_graph_dict_directly_merge_in_gateway)
    assert set([node.name for node in graph.origin_nodes]) == {'pod0'}

    node_pod0 = graph.origin_nodes[0]
    assert node_pod0.name == 'pod0'
    assert len(node_pod0.outgoing_nodes) == 2
    outgoing_pod0_list = [node.name for node in node_pod0.outgoing_nodes]
    assert node_pod0.number_of_parts == 1

    node_pod1 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod1')]
    assert node_pod1.name == 'pod1'
    assert len(node_pod1.outgoing_nodes) == 1
    assert node_pod1.outgoing_nodes[0].name == 'merger'
    assert node_pod1.number_of_parts == 1

    node_pod2 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod2')]
    assert node_pod2.name == 'pod2'
    assert len(node_pod2.outgoing_nodes) == 1
    assert node_pod2.outgoing_nodes[0].name == 'merger'
    assert node_pod2.number_of_parts == 1
    assert id(node_pod1.outgoing_nodes[0]) == id(node_pod2.outgoing_nodes[0])

    merger_pod = node_pod1.outgoing_nodes[0]
    assert merger_pod.name == 'merger'
    assert merger_pod.number_of_parts == 2
    assert len(merger_pod.outgoing_nodes) == 0


def test_topology_graph_build_merge_in_last_pod(
    merge_graph_dict_directly_merge_in_last_pod,
):
    graph = TopologyGraph(merge_graph_dict_directly_merge_in_last_pod)
    assert set([node.name for node in graph.origin_nodes]) == {'pod0'}

    node_pod0 = graph.origin_nodes[0]
    assert node_pod0.number_of_parts == 1
    assert len(node_pod0.outgoing_nodes) == 2
    outgoing_pod0_list = [node.name for node in node_pod0.outgoing_nodes]

    node_pod1 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod1')]
    assert node_pod1.number_of_parts == 1
    assert len(node_pod1.outgoing_nodes) == 1
    assert node_pod1.outgoing_nodes[0].name == 'merger'

    node_pod2 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod2')]
    assert node_pod2.number_of_parts == 1
    assert len(node_pod2.outgoing_nodes) == 1
    assert node_pod2.outgoing_nodes[0].name == 'merger'

    assert id(node_pod1.outgoing_nodes[0]) == id(node_pod2.outgoing_nodes[0])

    merger_pod = node_pod1.outgoing_nodes[0]
    assert merger_pod.name == 'merger'
    assert len(merger_pod.outgoing_nodes) == 1
    assert merger_pod.number_of_parts == 2

    pod_last_pod = merger_pod.outgoing_nodes[0]
    assert pod_last_pod.name == 'pod_last'
    assert len(pod_last_pod.outgoing_nodes) == 0
    assert pod_last_pod.number_of_parts == 1


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
    outgoing_pod0_list = [node.name for node in node_pod0.outgoing_nodes]

    node_pod1 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod1')]
    assert node_pod1.number_of_parts == 1
    assert len(node_pod1.outgoing_nodes) == 0
    node_pod2 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod2')]
    assert len(node_pod2.outgoing_nodes) == 1
    assert node_pod2.number_of_parts == 1

    node_pod3 = node_pod2.outgoing_nodes[0]
    assert node_pod3.name == 'pod3'
    assert node_pod3.number_of_parts == 1
    assert len(node_pod3.outgoing_nodes) == 1
    assert node_pod3.outgoing_nodes[0].name == 'merger'

    node_pod4 = graph.origin_nodes[node_names_list.index('pod4')]
    assert node_pod4.number_of_parts == 1
    assert len(node_pod4.outgoing_nodes) == 1
    node_pod5 = node_pod4.outgoing_nodes[0]
    assert node_pod5.number_of_parts == 1
    assert node_pod5.name == 'pod5'
    assert len(node_pod5.outgoing_nodes) == 1
    assert node_pod5.outgoing_nodes[0].name == 'merger'

    assert id(node_pod3.outgoing_nodes[0]) == id(node_pod5.outgoing_nodes[0])

    merger_pod = node_pod3.outgoing_nodes[0]
    assert merger_pod.name == 'merger'
    assert len(merger_pod.outgoing_nodes) == 1
    assert merger_pod.number_of_parts == 2

    pod_last_pod = merger_pod.outgoing_nodes[0]
    assert pod_last_pod.name == 'pod_last'
    assert len(pod_last_pod.outgoing_nodes) == 0
    assert pod_last_pod.number_of_parts == 1

    node_pod6 = graph.origin_nodes[node_names_list.index('pod6')]
    assert node_pod6.name == 'pod6'
    assert node_pod6.number_of_parts == 1
    assert len(node_pod6.outgoing_nodes) == 0


class DummyMockConnectionPool:
    def __init__(self, *args, **kwargs):
        self.args = None

    async def send(self, msg, pod) -> str:
        import random

        await asyncio.sleep(1 / (random.randint(1, 3) * 10))
        clientid = msg[0:7]
        return msg + f'-{clientid}-{pod}'


class DummyMockGatewayRuntime:
    def __init__(self, graph_representation, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection_pool = DummyMockConnectionPool(*args, **kwargs)
        self.graph = TopologyGraph(graph_representation)

    async def receive_from_client(self, client_id, msg):
        graph = copy.deepcopy(self.graph)
        # important that the gateway needs to have an instance of the graph per request
        tasks = []
        for origin_node in graph.origin_nodes:
            leaf_tasks = origin_node.get_leaf_tasks(self.connection_pool, msg, None)
            # Every origin node returns a set of tasks that are the ones corresponding to the leafs of each of their subtrees that unwrap all the previous tasks.
            # It starts like a chain of waiting for tasks from previous nodes
            tasks.extend(leaf_tasks)
        resp = await asyncio.gather(*tasks)
        return client_id, resp


@pytest.mark.asyncio
async def test_message_ordering_linear_graph(linear_graph_dict):
    runtime = DummyMockGatewayRuntime(linear_graph_dict)
    resps = await asyncio.gather(
        runtime.receive_from_client(0, 'client0-Request'),
        runtime.receive_from_client(1, 'client1-Request'),
        runtime.receive_from_client(2, 'client2-Request'),
        runtime.receive_from_client(3, 'client3-Request'),
        runtime.receive_from_client(4, 'client4-Request'),
        runtime.receive_from_client(5, 'client5-Request'),
        runtime.receive_from_client(6, 'client6-Request'),
        runtime.receive_from_client(7, 'client7-Request'),
        runtime.receive_from_client(8, 'client8-Request'),
        runtime.receive_from_client(9, 'client9-Request'),
    )
    assert len(resps) == 10
    for client_id, client_resps in resps:
        assert len(client_resps) == 1
        assert (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod1-client{client_id}-pod2-client{client_id}-pod3'
            == client_resps[0]
        )


@pytest.mark.asyncio
async def test_message_ordering_bifurcation_graph(bifurcation_graph_dict):
    runtime = DummyMockGatewayRuntime(bifurcation_graph_dict)
    resps = await asyncio.gather(
        runtime.receive_from_client(0, 'client0-Request'),
        runtime.receive_from_client(1, 'client1-Request'),
        runtime.receive_from_client(2, 'client2-Request'),
        runtime.receive_from_client(3, 'client3-Request'),
        runtime.receive_from_client(4, 'client4-Request'),
        runtime.receive_from_client(5, 'client5-Request'),
        runtime.receive_from_client(6, 'client6-Request'),
        runtime.receive_from_client(7, 'client7-Request'),
        runtime.receive_from_client(8, 'client8-Request'),
        runtime.receive_from_client(9, 'client9-Request'),
    )
    assert len(resps) == 10
    for client_id, client_resps in resps:
        assert len(client_resps) == 4
        sorted_clients_resps = list(sorted(client_resps))

        assert (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod1'
            == sorted_clients_resps[0]
        )
        assert (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod2-client{client_id}-pod3'
            == sorted_clients_resps[1]
        )
        assert (
            f'client{client_id}-Request-client{client_id}-pod4-client{client_id}-pod5'
            == sorted_clients_resps[2]
        )
        assert (
            f'client{client_id}-Request-client{client_id}-pod6'
            == sorted_clients_resps[3]
        )


@pytest.mark.asyncio
async def test_message_ordering_merge_in_gateway_graph(
    merge_graph_dict_directly_merge_in_gateway,
):
    runtime = DummyMockGatewayRuntime(merge_graph_dict_directly_merge_in_gateway)
    resps = await asyncio.gather(
        runtime.receive_from_client(0, 'client0-Request'),
        runtime.receive_from_client(1, 'client1-Request'),
        runtime.receive_from_client(2, 'client2-Request'),
        runtime.receive_from_client(3, 'client3-Request'),
        runtime.receive_from_client(4, 'client4-Request'),
        runtime.receive_from_client(5, 'client5-Request'),
        runtime.receive_from_client(6, 'client6-Request'),
        runtime.receive_from_client(7, 'client7-Request'),
        runtime.receive_from_client(8, 'client8-Request'),
        runtime.receive_from_client(9, 'client9-Request'),
    )
    assert len(resps) == 10
    for client_id, client_resps in resps:
        assert len(client_resps) == 2
        assert (
            None in client_resps
        )  # at the merge branch, only responds to the last part
        pod2_path = (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod2-client{client_id}-merger'
            in client_resps
        )
        pod1_path = (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod1-client{client_id}-merger'
            in client_resps
        )
        # TODO: need to add logic to merge messages
        assert pod1_path or pod2_path


@pytest.mark.asyncio
async def test_message_ordering_merge_in_last_pod_graph(
    merge_graph_dict_directly_merge_in_last_pod,
):
    runtime = DummyMockGatewayRuntime(merge_graph_dict_directly_merge_in_last_pod)
    resps = await asyncio.gather(
        runtime.receive_from_client(0, 'client0-Request'),
        runtime.receive_from_client(1, 'client1-Request'),
        runtime.receive_from_client(2, 'client2-Request'),
        runtime.receive_from_client(3, 'client3-Request'),
        runtime.receive_from_client(4, 'client4-Request'),
        runtime.receive_from_client(5, 'client5-Request'),
        runtime.receive_from_client(6, 'client6-Request'),
        runtime.receive_from_client(7, 'client7-Request'),
        runtime.receive_from_client(8, 'client8-Request'),
        runtime.receive_from_client(9, 'client9-Request'),
    )
    assert len(resps) == 10
    for client_id, client_resps in resps:
        assert len(client_resps) == 2
        assert (
            None in client_resps
        )  # at the merge branch, only responds to the last part
        pod2_path = (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod2-client{client_id}-merger-client{client_id}-pod_last'
            in client_resps
        )
        pod1_path = (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod1-client{client_id}-merger-client{client_id}-pod_last'
            in client_resps
        )
        # TODO: need to add logic to merge messages
        assert pod1_path or pod2_path


@pytest.mark.asyncio
async def test_message_ordering_complete_graph(complete_graph_dict):
    runtime = DummyMockGatewayRuntime(complete_graph_dict)
    resps = await asyncio.gather(
        runtime.receive_from_client(0, 'client0-Request'),
        runtime.receive_from_client(1, 'client1-Request'),
        runtime.receive_from_client(2, 'client2-Request'),
        runtime.receive_from_client(3, 'client3-Request'),
        runtime.receive_from_client(4, 'client4-Request'),
        runtime.receive_from_client(5, 'client5-Request'),
        runtime.receive_from_client(6, 'client6-Request'),
        runtime.receive_from_client(7, 'client7-Request'),
        runtime.receive_from_client(8, 'client8-Request'),
        runtime.receive_from_client(9, 'client9-Request'),
    )
    assert len(resps) == 10
    for client_id, client_resps in resps:
        assert len(client_resps) == 4
        assert (
            None in client_resps
        )  # at the merge branch, only responds to the last part
        filtered_client_resps = [resp for resp in client_resps if resp is not None]
        assert len(filtered_client_resps) == 3
        sorted_filtered_client_resps = list(sorted(filtered_client_resps))
        assert (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod1'
            == sorted_filtered_client_resps[0]
        )
        assert (
            f'client{client_id}-Request-client{client_id}-pod6'
            == sorted_filtered_client_resps[2]
        )

        pod2_path = (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod2-client{client_id}-pod3-client{client_id}-merger-client{client_id}-pod_last'
            == sorted_filtered_client_resps[1]
        )
        pod4_path = (
            f'client{client_id}-Request-client{client_id}-pod4-client{client_id}-pod5-client{client_id}-merger-client{client_id}-pod_last'
            == sorted_filtered_client_resps[1]
        )

        assert pod2_path or pod4_path

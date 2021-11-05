import pytest

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
    assert [node.node_name for node in graph.origin_nodes] == ['pod0']
    assert graph.origin_nodes[0].node_name == 'pod0'
    assert graph.origin_nodes[0].number_of_parts == 1
    assert graph.origin_nodes[0].outgoing_nodes[0].node_name == 'pod1'
    assert graph.origin_nodes[0].outgoing_nodes[0].number_of_parts == 1
    assert graph.origin_nodes[0].outgoing_nodes[0].outgoing_nodes[0].node_name == 'pod2'
    assert (
        graph.origin_nodes[0].outgoing_nodes[0].outgoing_nodes[0].number_of_parts == 1
    )
    assert (
        graph.origin_nodes[0]
        .outgoing_nodes[0]
        .outgoing_nodes[0]
        .outgoing_nodes[0]
        .node_name
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
    node_names_list = [node.node_name for node in graph.origin_nodes]
    assert set(node_names_list) == {'pod0', 'pod4', 'pod6'}
    assert len(graph.origin_nodes[node_names_list.index('pod0')].outgoing_nodes) == 2
    assert set(
        [
            node.node_name
            for node in graph.origin_nodes[node_names_list.index('pod0')].outgoing_nodes
        ]
    ) == {'pod1', 'pod2'}

    node_pod0 = graph.origin_nodes[node_names_list.index('pod0')]
    assert node_pod0.node_name == 'pod0'
    assert node_pod0.number_of_parts == 1
    outgoing_pod0_list = [node.node_name for node in node_pod0.outgoing_nodes]

    node_pod1 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod1')]
    assert node_pod1.node_name == 'pod1'
    assert node_pod1.number_of_parts == 1
    assert len(node_pod1.outgoing_nodes) == 0
    node_pod2 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod2')]
    assert node_pod2.node_name == 'pod2'
    assert node_pod2.number_of_parts == 1
    assert len(node_pod2.outgoing_nodes) == 1

    node_pod3 = node_pod2.outgoing_nodes[0]
    assert node_pod3.node_name == 'pod3'
    assert node_pod3.number_of_parts == 1
    assert len(node_pod3.outgoing_nodes) == 0

    node_pod4 = graph.origin_nodes[node_names_list.index('pod4')]
    assert node_pod4.node_name == 'pod4'
    assert node_pod4.number_of_parts == 1
    assert len(node_pod4.outgoing_nodes) == 1
    assert set(
        [
            node.node_name
            for node in graph.origin_nodes[node_names_list.index('pod4')].outgoing_nodes
        ]
    ) == {'pod5'}

    node_pod4 = graph.origin_nodes[node_names_list.index('pod4')]
    assert node_pod4.number_of_parts == 1
    node_pod5 = node_pod4.outgoing_nodes[0]
    assert node_pod5.node_name == 'pod5'
    assert node_pod5.number_of_parts == 1
    assert len(node_pod5.outgoing_nodes) == 0

    node_pod6 = graph.origin_nodes[node_names_list.index('pod6')]
    assert node_pod6.node_name == 'pod6'
    assert len(node_pod6.outgoing_nodes) == 0
    assert node_pod6.number_of_parts == 1
    assert set([node.node_name for node in node_pod6.outgoing_nodes]) == set()


def test_topology_graph_build_merge_in_gateway(
    merge_graph_dict_directly_merge_in_gateway,
):
    graph = TopologyGraph(merge_graph_dict_directly_merge_in_gateway)
    assert set([node.node_name for node in graph.origin_nodes]) == {'pod0'}

    node_pod0 = graph.origin_nodes[0]
    assert node_pod0.node_name == 'pod0'
    assert len(node_pod0.outgoing_nodes) == 2
    outgoing_pod0_list = [node.node_name for node in node_pod0.outgoing_nodes]
    assert node_pod0.number_of_parts == 1

    node_pod1 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod1')]
    assert node_pod1.node_name == 'pod1'
    assert len(node_pod1.outgoing_nodes) == 1
    assert node_pod1.outgoing_nodes[0].node_name == 'merger'
    assert node_pod1.number_of_parts == 1

    node_pod2 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod2')]
    assert node_pod2.node_name == 'pod2'
    assert len(node_pod2.outgoing_nodes) == 1
    assert node_pod2.outgoing_nodes[0].node_name == 'merger'
    assert node_pod2.number_of_parts == 1
    assert id(node_pod1.outgoing_nodes[0]) == id(node_pod2.outgoing_nodes[0])

    merger_pod = node_pod1.outgoing_nodes[0]
    assert merger_pod.node_name == 'merger'
    assert merger_pod.number_of_parts == 2
    assert len(merger_pod.outgoing_nodes) == 0


def test_topology_graph_build_merge_in_last_pod(
    merge_graph_dict_directly_merge_in_last_pod,
):
    graph = TopologyGraph(merge_graph_dict_directly_merge_in_last_pod)
    assert set([node.node_name for node in graph.origin_nodes]) == {'pod0'}

    node_pod0 = graph.origin_nodes[0]
    assert node_pod0.number_of_parts == 1
    assert len(node_pod0.outgoing_nodes) == 2
    outgoing_pod0_list = [node.node_name for node in node_pod0.outgoing_nodes]

    node_pod1 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod1')]
    assert node_pod1.number_of_parts == 1
    assert len(node_pod1.outgoing_nodes) == 1
    assert node_pod1.outgoing_nodes[0].node_name == 'merger'

    node_pod2 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod2')]
    assert node_pod2.number_of_parts == 1
    assert len(node_pod2.outgoing_nodes) == 1
    assert node_pod2.outgoing_nodes[0].node_name == 'merger'

    assert id(node_pod1.outgoing_nodes[0]) == id(node_pod2.outgoing_nodes[0])

    merger_pod = node_pod1.outgoing_nodes[0]
    assert merger_pod.node_name == 'merger'
    assert len(merger_pod.outgoing_nodes) == 1
    assert merger_pod.number_of_parts == 2

    pod_last_pod = merger_pod.outgoing_nodes[0]
    assert pod_last_pod.node_name == 'pod_last'
    assert len(pod_last_pod.outgoing_nodes) == 0
    assert pod_last_pod.number_of_parts == 1


def test_topology_graph_build_complete(complete_graph_dict):
    graph = TopologyGraph(complete_graph_dict)
    assert set([node.node_name for node in graph.origin_nodes]) == {
        'pod0',
        'pod4',
        'pod6',
    }
    node_names_list = [node.node_name for node in graph.origin_nodes]

    node_pod0 = graph.origin_nodes[node_names_list.index('pod0')]
    assert node_pod0.number_of_parts == 1
    outgoing_pod0_list = [node.node_name for node in node_pod0.outgoing_nodes]

    node_pod1 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod1')]
    assert node_pod1.number_of_parts == 1
    assert len(node_pod1.outgoing_nodes) == 0
    node_pod2 = node_pod0.outgoing_nodes[outgoing_pod0_list.index('pod2')]
    assert len(node_pod2.outgoing_nodes) == 1
    assert node_pod2.number_of_parts == 1

    node_pod3 = node_pod2.outgoing_nodes[0]
    assert node_pod3.node_name == 'pod3'
    assert node_pod3.number_of_parts == 1
    assert len(node_pod3.outgoing_nodes) == 1
    assert node_pod3.outgoing_nodes[0].node_name == 'merger'

    node_pod4 = graph.origin_nodes[node_names_list.index('pod4')]
    assert node_pod4.number_of_parts == 1
    assert len(node_pod4.outgoing_nodes) == 1
    node_pod5 = node_pod4.outgoing_nodes[0]
    assert node_pod5.number_of_parts == 1
    assert node_pod5.node_name == 'pod5'
    assert len(node_pod5.outgoing_nodes) == 1
    assert node_pod5.outgoing_nodes[0].node_name == 'merger'

    assert id(node_pod3.outgoing_nodes[0]) == id(node_pod5.outgoing_nodes[0])

    merger_pod = node_pod3.outgoing_nodes[0]
    assert merger_pod.node_name == 'merger'
    assert len(merger_pod.outgoing_nodes) == 1
    assert merger_pod.number_of_parts == 2

    pod_last_pod = merger_pod.outgoing_nodes[0]
    assert pod_last_pod.node_name == 'pod_last'
    assert len(pod_last_pod.outgoing_nodes) == 0
    assert pod_last_pod.number_of_parts == 1

    node_pod6 = graph.origin_nodes[node_names_list.index('pod6')]
    assert node_pod6.node_name == 'pod6'
    assert node_pod6.number_of_parts == 1
    assert len(node_pod6.outgoing_nodes) == 0

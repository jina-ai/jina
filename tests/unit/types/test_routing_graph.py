from google.protobuf import json_format

from jina.types.routing.graph import RoutingGraph
from jina.proto import jina_pb2


def get_next_routes(routing):
    routing = RoutingGraph.from_dict(routing)
    return routing.get_next_targets()


def test_single_routing():
    graph = RoutingGraph()
    graph.add_pod('pod0', '0.0.0.0', 1230)
    graph.active_pod = 'pod0'
    next_routes = graph.get_next_targets()

    assert len(next_routes) == 0


def test_simple_routing():
    graph = RoutingGraph()
    graph.add_pod('pod0', '0.0.0.0', 1230)
    graph.add_pod('pod1', '0.0.0.0', 1231)
    graph.add_edge('pod0', 'pod1')
    graph.active_pod = 'pod0'
    next_routes = graph.get_next_targets()

    assert len(next_routes) == 1
    assert next_routes[0].active_pod == 'pod1'


def test_double_routing():
    graph = RoutingGraph()
    graph.add_pod('pod0', '0.0.0.0', 1230)
    graph.add_pod('pod1', '0.0.0.0', 1231)
    graph.add_pod('pod2', '0.0.0.0', 1232)
    graph.add_pod('pod3', '0.0.0.0', 1233)
    graph.add_edge('pod0', 'pod1')
    graph.add_edge('pod0', 'pod2')
    graph.add_edge('pod1', 'pod3')
    graph.add_edge('pod2', 'pod3')
    graph.active_pod = 'pod0'
    next_routes = graph.get_next_targets()

    assert len(next_routes) == 2
    assert next_routes[0].active_pod == 'pod1'
    assert next_routes[1].active_pod == 'pod2'


def test_nested_routing():

    graph = RoutingGraph()
    graph.add_pod('pod0', '0.0.0.0', 1230)
    graph.add_pod('pod1', '0.0.0.0', 1231)
    graph.add_pod('pod2', '0.0.0.0', 1232)
    graph.add_pod('pod3', '0.0.0.0', 1233)
    graph.add_pod('pod4', '0.0.0.0', 1233)
    graph.add_edge('pod0', 'pod1')
    graph.add_edge('pod0', 'pod2')
    graph.add_edge('pod1', 'pod3')
    graph.add_edge('pod2', 'pod4')
    graph.add_edge('pod3', 'pod4')
    graph.active_pod = 'pod0'
    next_routes = graph.get_next_targets()

    assert len(next_routes) == 2
    assert next_routes[0].active_pod == 'pod1'
    assert next_routes[1].active_pod == 'pod2'

    graph.active_pod = 'pod1'
    next_routes = graph.get_next_targets()

    assert len(next_routes) == 1
    assert next_routes[0].active_pod == 'pod3'

    graph.active_pod = 'pod2'
    next_routes = graph.get_next_targets()

    assert len(next_routes) == 1
    assert next_routes[0].active_pod == 'pod4'

    graph.active_pod = 'pod3'
    next_routes = graph.get_next_targets()

    assert len(next_routes) == 1
    assert next_routes[0].active_pod == 'pod4'

    graph.active_pod = 'pod4'
    next_routes = graph.get_next_targets()

    assert len(next_routes) == 0


def test_topological_sorting():

    graph = RoutingGraph()
    graph.add_pod('pod0', '0.0.0.0', 1230)
    graph.add_pod('pod1', '0.0.0.0', 1231)
    graph.add_pod('pod2', '0.0.0.0', 1232)
    graph.add_pod('pod3', '0.0.0.0', 1233)
    graph.add_pod('pod4', '0.0.0.0', 1233)
    graph.add_edge('pod0', 'pod1')
    graph.add_edge('pod0', 'pod2')
    graph.add_edge('pod1', 'pod3')
    graph.add_edge('pod2', 'pod4')
    graph.add_edge('pod3', 'pod4')
    graph.active_pod = 'pod0'
    topological_sorting = graph._topological_sort()

    assert topological_sorting[0] == 'pod0'
    assert topological_sorting[1] in ['pod1', 'pod2']
    assert topological_sorting[2] in ['pod1', 'pod2', 'pod3']
    assert topological_sorting[3] in ['pod2', 'pod3']
    assert topological_sorting[4] == 'pod4'
    assert topological_sorting == ['pod0', 'pod2', 'pod1', 'pod3', 'pod4']


def test_cycle():

    graph = RoutingGraph()
    graph.add_pod('pod0', '0.0.0.0', 1230)
    graph.add_pod('pod1', '0.0.0.0', 1231)
    graph.add_edge('pod0', 'pod1')
    graph.add_edge('pod1', 'pod0')
    graph.active_pod = 'pod0'
    assert not graph.is_acyclic()


def test_no_cycle():

    graph = RoutingGraph()
    graph.add_pod('pod0', '0.0.0.0', 1230)
    graph.add_pod('pod1', '0.0.0.0', 1231)
    graph.add_pod('pod2', '0.0.0.0', 1232)
    graph.add_pod('pod3', '0.0.0.0', 1233)
    graph.add_pod('pod4', '0.0.0.0', 1233)
    graph.add_edge('pod2', 'pod1')
    graph.add_edge('pod1', 'pod0')
    graph.add_edge('pod0', 'pod3')
    graph.add_edge('pod3', 'pod4')
    graph.active_pod = 'pod0'

    assert graph.is_acyclic()

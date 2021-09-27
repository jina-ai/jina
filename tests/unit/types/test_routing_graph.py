from jina.types.routing.table import RoutingTable


def test_single_routing():
    graph = RoutingTable()
    graph.add_pod('executor0', '0.0.0.0', 1230, 1233, '')
    graph.active_pod = 'executor0'
    next_routes = graph.get_next_targets()

    assert len(next_routes) == 0


def test_simple_routing():
    graph = RoutingTable()
    graph.add_pod('executor0', '0.0.0.0', 1230, 1232, '')
    graph.add_pod('executor1', '0.0.0.0', 1231, 1233, '')
    graph.add_edge('executor0', 'executor1')
    graph.active_pod = 'executor0'
    next_routes = graph.get_next_targets()

    assert len(next_routes) == 1
    assert next_routes[0][0].active_pod == 'executor1'


def test_double_routing():
    graph = RoutingTable()
    graph.add_pod('executor0', '0.0.0.0', 1230, 1234, '')
    graph.add_pod('executor1', '0.0.0.0', 1231, 1235, '')
    graph.add_pod('executor2', '0.0.0.0', 1232, 1236, '')
    graph.add_pod('executor3', '0.0.0.0', 1233, 1237, '')
    graph.add_edge('executor0', 'executor1')
    graph.add_edge('executor0', 'executor2')
    graph.add_edge('executor1', 'executor3')
    graph.add_edge('executor2', 'executor3')
    graph.active_pod = 'executor0'
    next_routes = graph.get_next_targets()

    assert len(next_routes) == 2
    assert next_routes[0][0].active_pod == 'executor1'
    assert next_routes[1][0].active_pod == 'executor2'


def test_nested_routing():
    graph = RoutingTable()
    graph.add_pod('executor0', '0.0.0.0', 1230, 1234, '')
    graph.add_pod('executor1', '0.0.0.0', 1231, 1235, '')
    graph.add_pod('executor2', '0.0.0.0', 1232, 1236, '')
    graph.add_pod('executor3', '0.0.0.0', 1233, 1237, '')
    graph.add_pod('executor4', '0.0.0.0', 1233, 1238, '')
    graph.add_edge('executor0', 'executor1')
    graph.add_edge('executor0', 'executor2')
    graph.add_edge('executor1', 'executor3')
    graph.add_edge('executor2', 'executor4')
    graph.add_edge('executor3', 'executor4')
    graph.active_pod = 'executor0'
    next_routes = graph.get_next_targets()

    assert len(next_routes) == 2
    assert next_routes[0][0].active_pod == 'executor1'
    assert next_routes[1][0].active_pod == 'executor2'

    graph.active_pod = 'executor1'
    next_routes = graph.get_next_targets()

    assert len(next_routes) == 1
    assert next_routes[0][0].active_pod == 'executor3'

    graph.active_pod = 'executor2'
    next_routes = graph.get_next_targets()

    assert len(next_routes) == 1
    assert next_routes[0][0].active_pod == 'executor4'

    graph.active_pod = 'executor3'
    next_routes = graph.get_next_targets()

    assert len(next_routes) == 1
    assert next_routes[0][0].active_pod == 'executor4'

    graph.active_pod = 'executor4'
    next_routes = graph.get_next_targets()

    assert len(next_routes) == 0


def test_topological_sorting():
    graph = RoutingTable()
    graph.add_pod('executor0', '0.0.0.0', 1230, 1234, '')
    graph.add_pod('executor1', '0.0.0.0', 1231, 1235, '')
    graph.add_pod('executor2', '0.0.0.0', 1232, 1236, '')
    graph.add_pod('executor3', '0.0.0.0', 1233, 1237, '')
    graph.add_pod('executor4', '0.0.0.0', 1233, 1238, '')
    graph.add_edge('executor0', 'executor1')
    graph.add_edge('executor0', 'executor2')
    graph.add_edge('executor1', 'executor3')
    graph.add_edge('executor2', 'executor4')
    graph.add_edge('executor3', 'executor4')
    graph.active_pod = 'executor0'
    topological_sorting = graph._topological_sort()

    assert topological_sorting[0] == 'executor0'
    assert topological_sorting[1] in ['executor1', 'executor2']
    assert topological_sorting[2] in ['executor1', 'executor2', 'executor3']
    assert topological_sorting[3] in ['executor2', 'executor3']
    assert topological_sorting[4] == 'executor4'


def test_cycle():
    graph = RoutingTable()
    graph.add_pod('executor0', '0.0.0.0', 1230, 1232, '')
    graph.add_pod('executor1', '0.0.0.0', 1231, 1233, '')
    graph.add_edge('executor0', 'executor1')
    graph.add_edge('executor1', 'executor0')
    graph.active_pod = 'executor0'
    assert not graph.is_acyclic()


def test_no_cycle():
    graph = RoutingTable()
    graph.add_pod('executor0', '0.0.0.0', 1230, 1234, '')
    graph.add_pod('executor1', '0.0.0.0', 1231, 1235, '')
    graph.add_pod('executor2', '0.0.0.0', 1232, 1236, '')
    graph.add_pod('executor3', '0.0.0.0', 1233, 1237, '')
    graph.add_pod('executor4', '0.0.0.0', 1233, 1238, '')
    graph.add_edge('executor2', 'executor1')
    graph.add_edge('executor1', 'executor0')
    graph.add_edge('executor0', 'executor3')
    graph.add_edge('executor3', 'executor4')
    graph.active_pod = 'executor0'

    assert graph.is_acyclic()

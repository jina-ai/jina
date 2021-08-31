from daemon.models.ports import PortMapping, PortMappings

d = [
    {
        'pod_name': 'query_indexer',
        'pea_name': 'query_indexer/head',
        'ports': {'port_in': 1234, 'port_out': 2345},
    },
    {
        'pod_name': 'query_indexer',
        'pea_name': 'query_indexer/tail',
        'ports': {'port_in': 3456, 'port_out': 4567},
    },
    {
        'pod_name': 'encoder',
        'pea_name': 'encoder/pea-0',
        'ports': {'port_in': 12345},
    },
]


def test_port_mapping():
    p = PortMapping(**d[0])
    assert p.pod_name == 'query_indexer'
    assert p.pea_name == 'query_indexer/head'
    assert p.ports.port_in == 1234


def test_port_mappings():
    p = PortMappings.parse_obj(d)
    assert 'query_indexer' in p.pod_names
    assert 'encoder' in p.pod_names
    assert 'query_indexer/head' in p.pea_names
    assert 'query_indexer/tail' in p.pea_names
    assert p['encoder/pea-0'].ports.port_in == 12345
    assert p.ports == [1234, 2345, 3456, 4567, 12345]

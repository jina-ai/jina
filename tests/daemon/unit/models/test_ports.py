from daemon.models.ports import PortMapping, PortMappings

d = [
    {
        'deployment_name': 'query_indexer',
        'pea_name': 'query_indexer/head',
        'ports': {'port_in': 1234},
    },
    {
        'deployment_name': 'query_indexer',
        'pea_name': 'query_indexer/tail',
        'ports': {'port_in': 3456},
    },
    {
        'deployment_name': 'encoder',
        'pea_name': 'encoder/pea-0',
        'ports': {'port_in': 12345},
    },
]


def test_port_mapping():
    p = PortMapping(**d[0])
    assert p.deployment_name == 'query_indexer'
    assert p.pea_name == 'query_indexer/head'
    assert p.ports.port_in == 1234


def test_port_mappings():
    p = PortMappings.parse_obj(d)
    assert 'query_indexer' in p.deployment_names
    assert 'encoder' in p.deployment_names
    assert 'query_indexer/head' in p.pea_names
    assert 'query_indexer/tail' in p.pea_names
    assert p['encoder/pea-0'].ports.port_in == 12345
    assert p.ports == [1234, 3456, 12345]

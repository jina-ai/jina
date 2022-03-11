from daemon.models.ports import PortMapping, PortMappings

d = [
    {
        'deployment_name': 'query_indexer',
        'pod_name': 'query_indexer/head',
        'ports': {'port': 1234},
    },
    {
        'deployment_name': 'query_indexer',
        'pod_name': 'query_indexer/tail',
        'ports': {'port': 3456},
    },
    {
        'deployment_name': 'encoder',
        'pod_name': 'encoder/pod-0',
        'ports': {'port': 12345},
    },
]


def test_port_mapping():
    p = PortMapping(**d[0])
    assert p.deployment_name == 'query_indexer'
    assert p.pod_name == 'query_indexer/head'
    assert p.ports.port == 1234


def test_port_mappings():
    p = PortMappings.parse_obj(d)
    assert 'query_indexer' in p.deployment_names
    assert 'encoder' in p.deployment_names
    assert 'query_indexer/head' in p.pod_names
    assert 'query_indexer/tail' in p.pod_names
    assert p['encoder/pod-0'].ports.port == 12345
    assert p.ports == [1234, 3456, 12345]

from daemon import _get_app
from daemon.config import jinad_config


def test_get_app_flow(monkeypatch, common_endpoints, flow_endpoints):
    monkeypatch.setattr(jinad_config, 'CONTEXT', 'flow')
    routes = [(route.name, route.path) for route in _get_app().routes]
    assert sorted(routes) == sorted(common_endpoints + flow_endpoints)


def test_get_app_pod(monkeypatch, common_endpoints, pod_endpoints):
    monkeypatch.setattr(jinad_config, 'CONTEXT', 'pod')
    routes = [(route.name, route.path) for route in _get_app().routes]
    assert sorted(routes) == sorted(common_endpoints + pod_endpoints)


def test_get_app_pea(monkeypatch, common_endpoints, pea_endpoints):
    monkeypatch.setattr(jinad_config, 'CONTEXT', 'pea')
    routes = [(route.name, route.path) for route in _get_app().routes]
    assert sorted(routes) == sorted(common_endpoints + pea_endpoints)


def test_get_app_all(monkeypatch, common_endpoints, pea_endpoints, pod_endpoints, flow_endpoints):
    monkeypatch.setattr(jinad_config, 'CONTEXT', 'all')
    routes = [(route.name, route.path) for route in _get_app().routes]
    assert sorted(routes) == \
        sorted(common_endpoints + pea_endpoints + pod_endpoints + flow_endpoints)

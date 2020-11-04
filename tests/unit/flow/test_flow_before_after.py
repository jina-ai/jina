from jina.flow import Flow
from tests import random_docs


def test_flow():
    docs = random_docs(10)
    f = Flow().add(name='p1')

    with f:
        f.index(docs)
        assert f.num_pods == 2
        assert f._pod_nodes['p1'].num_peas == 1
        assert f.num_peas == 2


def test_flow_before():
    docs = random_docs(10)
    f = Flow().add(uses_before='_pass', name='p1')

    with f:
        f.index(docs)
        assert f.num_pods == 2
        assert f._pod_nodes['p1'].num_peas == 2
        assert f.num_peas == 3


def test_flow_after():
    docs = random_docs(10)
    f = Flow().add(uses_after='_pass', name='p1')

    with f:
        f.index(docs)
        assert f.num_pods == 2
        assert f._pod_nodes['p1'].num_peas == 2
        assert f.num_peas == 3


def test_flow_before_after():
    docs = random_docs(10)
    f = Flow().add(uses_before='_pass', uses_after='_pass', name='p1')

    with f:
        f.index(docs)
        assert f.num_pods == 2
        assert f._pod_nodes['p1'].num_peas == 3
        assert f.num_peas == 4

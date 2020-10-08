from jina.executors.evaluators.decorators import as_aggregator


def test_as_aggregator_method():
    class A:
        def __init__(self):
            self.num_documents = 0
            self.sum = 0

        @as_aggregator
        def f(self):
            return 10

    a = A()
    assert a.num_documents == 0
    assert a.sum == 0
    a.f()
    assert a.num_documents == 1
    assert a.sum == 10
    a.f()
    assert a.num_documents == 2
    assert a.sum == 20

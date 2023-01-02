from jina import Executor, requests, Flow, DocumentArray


def test_call_good_base_executor():
    class A(Executor):
        @requests
        def x(self, docs, **kwargs):
            for doc in docs:
                doc.tags['exec'] = 'A'

    class EnhancedExecutor(A):
        @requests
        def y(self, docs, **kwargs):
            for doc in docs:
                doc.tags['exec'] = 'Enhanced'

    assert EnhancedExecutor.__name__ in A.requests_by_class
    assert A.__name__ in EnhancedExecutor.requests_by_class
    f = Flow().add(uses=A)
    with f:
        ret = f.post(on='/', inputs=DocumentArray.empty(1))[0]

    assert ret.tags['exec'] == 'A'

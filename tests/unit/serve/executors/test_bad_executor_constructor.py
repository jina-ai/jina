from jina import Flow, Executor, requests

import pytest


class GoodExecutor(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @requests
    def foo(self, **kwargs):
        pass


class GoodExecutor2(Executor):
    def __init__(self, metas, requests, runtime_args, dynamic_batching):
        pass

    @requests
    def foo(self, docs, parameters, docs_matrix):
        pass


def test_bad_executor_constructor():
    # executor can be used as out of Flow as Python object
    exec1 = GoodExecutor()
    exec2 = GoodExecutor2({}, {}, {}, {})

    # can be used in the Flow
    with Flow().add(uses=GoodExecutor):
        pass

    with Flow().add(uses=GoodExecutor2):
        pass

    # bad executor due to mismatch on args
    with pytest.raises(TypeError):

        class BadExecutor1(Executor):
            def __init__(self):
                pass

            @requests
            def foo(self, **kwargs):
                pass

    with pytest.raises(TypeError):

        class BadExecutor2(Executor):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

            @requests
            def foo(self):
                pass

import os

import numpy as np
import pytest

from jina import Flow, Document
from jina.executors import GenericExecutor
from jina.executors.decorators import requests


class MyExecutor(GenericExecutor):
    @requests
    def foo(self, id):
        return [{'embedding': np.array([1, 2, 3])}] * len(id)

    @requests(on='SearchRequest')
    def bar(self, id):
        return [{'embedding': np.array([4, 5, 6])}] * len(id)

    @requests(on='UpdateRequest')
    def bar2(self, id):
        return [{'embedding': np.array([10, 11, 12])}] * len(id)


@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ,
    reason='locally it works fine, somehow this stuck on Github',
)
@pytest.mark.parametrize(
    'api, result',
    [['index', [1, 2, 3]], ['search', [4, 5, 6]], ['update', [10, 11, 12]]],
)
def test_generic_executor_with_routing_default(api, result, mocker):
    resp_mock = mocker.Mock()

    def validate(req):
        resp_mock()
        np.testing.assert_equal(req.docs[0].embedding, np.array(result))

    f = Flow().add(uses=MyExecutor)

    with f:
        getattr(f, api)(Document(), on_done=validate)

    resp_mock.assert_called()

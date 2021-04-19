import numpy as np

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


def test_generic_executor_with_routing(mocker):
    index_resp_mock = mocker.Mock()
    search_resp_mock = mocker.Mock()
    update_resp_mock = mocker.Mock()

    def validate_index_resp(req):
        index_resp_mock()
        np.testing.assert_equal(req.docs[0].embedding, np.array([1, 2, 3]))

    def validate_search_resp(req):
        search_resp_mock()
        np.testing.assert_equal(req.docs[0].embedding, np.array([4, 5, 6]))

    def validate_update_resp(req):
        update_resp_mock()
        np.testing.assert_equal(req.docs[0].embedding, np.array([10, 11, 12]))

    f = Flow().add(uses=MyExecutor)

    with f:
        f.index(Document(), on_done=validate_index_resp)

    with f:
        f.search(Document(), on_done=validate_search_resp)

    with f:
        f.update(Document(), on_done=validate_update_resp)

    index_resp_mock.assert_called()
    search_resp_mock.assert_called()
    update_resp_mock.assert_called()

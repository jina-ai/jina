import os
import shutil

import pytest

from jina.flow import Flow
from jina import Document, Executor, requests
from tests import validate_callback


def validate(req):
    assert len(req.docs) == 1
    assert len(req.docs[0].matches) == 5
    assert len(req.docs[0].matches[0].matches) == 5
    assert len(req.docs[0].matches[-1].matches) == 5
    assert len(req.docs[0].matches[0].matches[0].matches) == 0


class MyExecutor(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.doc = self.requests

    @requests(on='index')
    def index(self, docs, **kwargs):
        self.doc = docs[0]
        for match in self.doc.matches:
            for i in range(5):
                match.matches.append(Document())

        return self.doc


def test_high_order_matches(mocker):
    response_mock = mocker.Mock()

    f = Flow().add(uses=MyExecutor)

    with f:
        f.post(
            on='index',
            inputs=Document(matches=[Document() for i in range(5)]),
            on_done=response_mock,
        )

    validate_callback(response_mock, validate)


@pytest.mark.parametrize('restful', [False, True])
def test_high_order_matches_integrated(mocker, restful):

    response_mock = mocker.Mock()
    # this is equivalent to the last test but with simplified YAML spec.
    f = Flow(restful=restful).add(uses=MyExecutor)

    with f:
        f.post(
            on='index',
            inputs=Document(matches=[Document() for i in range(5)]),
            on_done=response_mock,
        )

    validate_callback(response_mock, validate)

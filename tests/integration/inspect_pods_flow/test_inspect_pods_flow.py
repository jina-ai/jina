import os

import pytest

from jina.types.score.map import NamedScoreMapping
from jina import Flow, Executor, DocumentArray, requests
from tests import random_docs, validate_callback


class DummyEvaluator1(Executor):
    tag = 1

    @requests(on=['/index'])
    def craft(self, docs, *args, **kwargs):
        tmp_dir = os.environ.get('TEST_EVAL_FLOW_TMPDIR')
        with open(f'{tmp_dir}/{self.tag}.txt', 'a') as fp:
            fp.write(f'{docs[0].id}')
        return None


class DummyEvaluator2(DummyEvaluator1):
    tag = 2


class DummyEvaluator3(DummyEvaluator1):
    tag = 3


docs = DocumentArray([x for x in random_docs(1)])
params = ['HANG', 'REMOVE', 'COLLECT']


def validate(ids, expect):
    assert len(ids) > 0
    for j in ids:
        tmp_dir = os.environ.get('TEST_EVAL_FLOW_TMPDIR')
        fname = f'{tmp_dir}/{j}.txt'
        assert os.path.exists(fname) == expect
        if expect:
            with open(fname) as fp:
                assert fp.read() != ''


@pytest.fixture
def temp_folder(tmpdir):
    os.environ['TEST_EVAL_FLOW_TMPDIR'] = str(tmpdir)
    yield
    del os.environ['TEST_EVAL_FLOW_TMPDIR']


@pytest.mark.parametrize('inspect', params)
@pytest.mark.parametrize('protocol', ['websocket', 'grpc'])
def test_flow1(inspect, protocol, temp_folder):
    f = Flow(protocol=protocol, inspect=inspect).add(
        uses=DummyEvaluator1,
        env={'TEST_EVAL_FLOW_TMPDIR': os.environ.get('TEST_EVAL_FLOW_TMPDIR')},
    )

    with f:
        f.post(on='/index', inputs=docs)


@pytest.mark.parametrize('inspect', params)
@pytest.mark.parametrize('protocol', ['websocket', 'grpc'])
def test_flow2(inspect, protocol, temp_folder):
    f = (
        Flow(protocol=protocol, inspect=inspect)
        .add()
        .inspect(
            uses=DummyEvaluator1,
            env={'TEST_EVAL_FLOW_TMPDIR': os.environ.get('TEST_EVAL_FLOW_TMPDIR')},
        )
    )

    with f:
        f.index(docs)

    validate([1], expect=f.args.inspect.is_keep)


@pytest.mark.parametrize('inspect', params)
@pytest.mark.parametrize('protocol', ['websocket', 'grpc'])
def test_flow3(inspect, protocol, temp_folder):
    env = {'TEST_EVAL_FLOW_TMPDIR': os.environ.get('TEST_EVAL_FLOW_TMPDIR')}

    f = (
        Flow(protocol=protocol, inspect=inspect)
        .add(name='p1')
        .inspect(uses='DummyEvaluator1', env=env)
        .add(name='p2', needs='gateway')
        .needs(['p1', 'p2'])
        .inspect(uses='DummyEvaluator2', env=env)
    )

    with f:
        f.index(docs)

    validate([1, 2], expect=f.args.inspect.is_keep)


@pytest.mark.parametrize('inspect', params)
@pytest.mark.parametrize('protocol', ['websocket', 'grpc'])
def test_flow4(inspect, protocol, temp_folder):
    env = {'TEST_EVAL_FLOW_TMPDIR': os.environ.get('TEST_EVAL_FLOW_TMPDIR')}

    f = (
        Flow(protocol=protocol, inspect=inspect)
        .add()
        .inspect(uses='DummyEvaluator1', env=env)
        .add()
        .inspect(uses='DummyEvaluator2', env=env)
        .add()
        .inspect(uses='DummyEvaluator3', env=env)
        .plot(build=True)
    )

    with f:
        f.index(docs)

    validate([1, 2, 3], expect=f.args.inspect.is_keep)


class AddEvaluationExecutor(Executor):
    @requests
    def transform(self, docs, *args, **kwargs):
        import time

        time.sleep(0.5)
        for doc in docs:
            doc.evaluations['evaluate'] = 10.0


@pytest.mark.repeat(5)
@pytest.mark.parametrize('protocol', ['websocket', 'grpc'])
def test_flow_returned_collect(protocol, mocker):
    # TODO(Joan): This test passes because we pass the `SlowExecutor` but I do not know how to make the `COLLECT` pod
    # use an specific executor.

    def validate_func(resp):
        for doc in resp.data.docs:
            assert len(NamedScoreMapping(doc.evaluations)) == 1
            assert NamedScoreMapping(doc.evaluations)['evaluate'].value == 10.0

    f = (
        Flow(protocol=protocol, inspect='COLLECT')
        .add()
        .inspect(
            uses=AddEvaluationExecutor,
        )
    )

    mock = mocker.Mock()
    with f:
        f.index(inputs=docs, on_done=mock)

    validate_callback(mock, validate_func)


@pytest.mark.repeat(5)
@pytest.mark.parametrize('inspect', ['HANG', 'REMOVE'])
@pytest.mark.parametrize('protocol', ['websocket', 'grpc'])
def test_flow_not_returned(inspect, protocol, mocker):
    def validate_func(resp):
        for doc in resp.data.docs:
            assert len(NamedScoreMapping(doc.evaluations)) == 0

    f = (
        Flow(protocol=protocol, inspect=inspect)
        .add()
        .inspect(
            uses=AddEvaluationExecutor,
        )
    )

    mock = mocker.Mock()
    with f:
        f.index(inputs=docs, on_done=mock)

    validate_callback(mock, validate_func)

import pytest

from jina.executors.crafters import BaseCrafter
from jina.flow import Flow
from tests import random_docs


class DummyEvaluator1(BaseCrafter):
    tag = 1

    def craft(self, id, *args, **kwargs):
        with open(f'tmp{self.tag}.txt', 'a') as fp:
            fp.write(f'{id}')
        return {}


class DummyEvaluator2(DummyEvaluator1):
    tag = 2


class DummyEvaluator3(DummyEvaluator1):
    tag = 3


docs = list(random_docs(1))


def test_flow1(tmpdir):
    f = Flow().add()

    with f:
        f.index(docs)


def test_flow2(tmpdir):
    f = Flow().add().eval(uses='DummyEvaluator1')

    with f:
        f.index(docs)

    for j in [1]:
        with open(f'tmp{j}.txt') as fp:
            assert fp.read() != ''


@pytest.mark.skip('this topology can not work at the moment, better EvalPod is needed')
def test_flow3(tmpdir):
    f = Flow().add(name='p1').eval(uses='DummyEvaluator1') \
        .add(name='p2', needs='gateway').needs(['p1', 'p2']).eval(uses='DummyEvaluator2')

    with f:
        f.index(docs)

    for j in [1, 2]:
        with open(f'tmp{j}.txt') as fp:
            assert fp.read() != ''


def test_flow4(tmpdir):
    f = Flow().add(name='p1').add(name='p2', needs='gateway').needs(['p1', 'p2']).eval(uses='DummyEvaluator1')

    with f:
        f.index(docs)

    for j in [1]:
        with open(f'tmp{j}.txt') as fp:
            assert fp.read() != ''


def test_flow5(tmpdir):
    f = Flow().add().eval(uses='DummyEvaluator1').add().eval(uses='DummyEvaluator2').add().eval(
        uses='DummyEvaluator3').plot(build=True)

    with f:
        f.index(docs)

    for j in [1, 2, 3]:
        with open(f'tmp{j}.txt') as fp:
            assert fp.read() != ''

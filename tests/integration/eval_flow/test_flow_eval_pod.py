import os

import pytest

from jina.executors.crafters import BaseCrafter
from jina.flow import Flow
from tests import random_docs, rm_files


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
params = ['HANG', 'REMOVE', 'COLLECT']


def validate(ids, expect):
    for j in ids:
        fname = f'tmp{j}.txt'
        assert os.path.exists(fname) == expect
        if expect:
            with open(fname) as fp:
                assert fp.read() != ''
        rm_files([fname])


@pytest.mark.parametrize('inspect', params)
def test_flow1(inspect):
    f = Flow(inspect=inspect).add()

    with f:
        f.index(docs)


@pytest.mark.parametrize('inspect', params)
def test_flow2(inspect):
    f = Flow(inspect=inspect).add().inspect(uses='DummyEvaluator1')

    with f:
        f.index(docs)

    validate([1], expect=f.args.inspect.is_keep)


@pytest.mark.parametrize('inspect', params)
def test_flow3(inspect):
    f = Flow(inspect=inspect).add(name='p1').inspect(uses='DummyEvaluator1') \
        .add(name='p2', needs='gateway').needs(['p1', 'p2']).inspect(uses='DummyEvaluator2')

    with f:
        f.index(docs)

    validate([1, 2], expect=f.args.inspect.is_keep)


@pytest.mark.parametrize('inspect', params)
def test_flow5(inspect):
    f = Flow(inspect=inspect).add().inspect(uses='DummyEvaluator1').add().inspect(
        uses='DummyEvaluator2').add().inspect(
        uses='DummyEvaluator3').plot(build=True)

    with f:
        f.index(docs)

    validate([1, 2, 3], expect=f.args.inspect.is_keep)

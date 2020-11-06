import pytest

from jina.excepts import ModelCheckpointNotExist
from jina.executors.crafters import BaseCrafter
from jina.executors.encoders import BaseEncoder
from jina.flow import Flow
from jina.proto import jina_pb2


class DummyCrafter(BaseCrafter):
    def craft(self, *args, **kwargs):
        return 1 / 0


class PretrainedModelEncoder(BaseEncoder):
    def post_init(self):
        raise ModelCheckpointNotExist


def test_bad_flow():
    def validate(req):
        assert req.status.code == jina_pb2.Status.ERROR
        assert req.routes[0].pod == 'r1'

    f = (Flow().add(name='r1', uses='!BaseCrafter')
         .add(name='r2', uses='!BaseEncoder')
         .add(name='r3', uses='!BaseEncoder'))

    # always test two times, make sure the flow still works after it fails on the first
    with f:
        f.index_lines(lines=['abbcs', 'efgh'], output_fn=validate)
        f.index_lines(lines=['abbcs', 'efgh'], output_fn=validate)


def test_bad_flow_customized():
    def validate(req):
        assert req.status.code == jina_pb2.Status.ERROR
        assert req.status.details[0].pod == 'r2'
        assert req.status.details[0].exception.startswith('ZeroDivisionError')

    f = (Flow().add(name='r1', uses='_pass')
         .add(name='r2', uses='!DummyCrafter')
         .add(name='r3', uses='!BaseEncoder'))

    with f:
        f.dry_run()

    # always test two times, make sure the flow still works after it fails on the first
    with f:
        f.index_lines(lines=['abbcs', 'efgh'], output_fn=validate)
        f.index_lines(lines=['abbcs', 'efgh'], output_fn=validate)


def test_except_with_parallel():
    def validate(req):
        assert req.status.code == jina_pb2.Status.ERROR
        assert len(req.status.details) == 2
        assert req.status.details[0].executor == 'DummyCrafter'
        assert req.status.details[1].executor == 'BaseEncoder'
        assert req.status.details[0].exception.startswith('ZeroDivisionError')
        assert req.status.details[1].exception.startswith('NotImplementedError')

    f = (Flow().add(name='r1', uses='_pass')
         .add(name='r2', uses='!DummyCrafter', parallel=3)
         .add(name='r3', uses='!BaseEncoder'))

    with f:
        f.dry_run()

    with f:
        f.index_lines(lines=['abbcs', 'efgh'], output_fn=validate)
        f.index_lines(lines=['abbcs', 'efgh'], output_fn=validate)


def test_except_pretrained_model_file():
    with pytest.raises(ModelCheckpointNotExist):
        with Flow().add(name='r2', uses='!PretrainedModelEncoder', parallel=1):
            pass

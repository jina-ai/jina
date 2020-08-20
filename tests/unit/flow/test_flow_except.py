import unittest

from jina.executors.crafters import BaseCrafter
from jina.flow import Flow
from jina.proto import jina_pb2
from tests import JinaTestCase


class DummyCrafter(BaseCrafter):
    def craft(self, *args, **kwargs):
        return 1 / 0


class FlowExceptTestCase(JinaTestCase):

    def test_bad_flow(self):
        def validate(req):
            assert req.status.code == jina_pb2.Status.ERROR
            assert req.status.details[0].pod == 'r1'

        f = (Flow().add(name='r1', uses='!BaseCrafter')
             .add(name='r2', uses='!BaseEncoder')
             .add(name='r3', uses='!BaseEncoder'))

        # always test two times, make sure the flow still works after it fails on the first
        with f:
            f.index_lines(lines=['abbcs', 'efgh'], output_fn=validate)
            f.index_lines(lines=['abbcs', 'efgh'], output_fn=validate)

    def test_bad_flow_customized(self):
        def validate(req):
            assert req.status.code == jina_pb2.Status.ERROR
            assert req.status.details[0].pod == 'r2'
            self.assertTrue(req.status.details[0].exception.startswith('ZeroDivisionError'))

        f = (Flow().add(name='r1', uses='_pass')
             .add(name='r2', uses='!DummyCrafter')
             .add(name='r3', uses='!BaseEncoder'))

        with f:
            f.dry_run()

        # always test two times, make sure the flow still works after it fails on the first
        with f:
            f.index_lines(lines=['abbcs', 'efgh'], output_fn=validate)
            f.index_lines(lines=['abbcs', 'efgh'], output_fn=validate)

    def test_except_with_parallel(self):
        def validate(req):
            assert req.status.code == jina_pb2.Status.ERROR
            assert len(req.status.details) == 2
            assert req.status.details[0].executor == 'DummyCrafter'
            assert req.status.details[1].executor == 'BaseEncoder'
            self.assertTrue(req.status.details[0].exception.startswith('ZeroDivisionError'))
            self.assertTrue(req.status.details[1].exception.startswith('NotImplementedError'))

        f = (Flow().add(name='r1', uses='_pass')
             .add(name='r2', uses='!DummyCrafter', parallel=3)
             .add(name='r3', uses='!BaseEncoder'))

        with f:
            f.dry_run()

        with f:
            f.index_lines(lines=['abbcs', 'efgh'], output_fn=validate)
            f.index_lines(lines=['abbcs', 'efgh'], output_fn=validate)


if __name__ == '__main__':
    unittest.main()

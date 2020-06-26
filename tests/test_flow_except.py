import unittest

from jina.executors.crafters import BaseDocCrafter
from jina.flow import Flow
from jina.proto import jina_pb2
from tests import JinaTestCase


class DummyCrafter(BaseDocCrafter):
    def craft(self, *args, **kwargs):
        return 1 / 0


class MyTestCase(JinaTestCase):

    def test_bad_flow(self):
        def validate(req):
            self.assertEqual(req.status.code, jina_pb2.Status.ERROR)
            self.assertEqual(req.status.details[0].pod, 'r1')

        f = (Flow().add(name='r1', yaml_path='!BaseDocCrafter')
             .add(name='r2', yaml_path='!BaseEncoder')
             .add(name='r3', yaml_path='!BaseEncoder'))

        # always test two times, make sure the flow still works after it fails on the first
        with f:
            f.index_lines(lines=['abbcs', 'efgh'], output_fn=validate)
            f.index_lines(lines=['abbcs', 'efgh'], output_fn=validate)

    def test_bad_flow_customized(self):
        def validate(req):
            self.assertEqual(req.status.code, jina_pb2.Status.ERROR)
            self.assertEqual(req.status.details[0].pod, 'r2')
            self.assertTrue(req.status.details[0].exception.startswith('ZeroDivisionError'))

        f = (Flow().add(name='r1', yaml_path='_forward')
             .add(name='r2', yaml_path='!DummyCrafter')
             .add(name='r3', yaml_path='!BaseEncoder'))

        with f:
            f.dry_run()

        # always test two times, make sure the flow still works after it fails on the first
        with f:
            f.index_lines(lines=['abbcs', 'efgh'], output_fn=validate)
            f.index_lines(lines=['abbcs', 'efgh'], output_fn=validate)

    def test_except_with_replicas(self):
        def validate(req):
            self.assertEqual(req.status.code, jina_pb2.Status.ERROR)
            self.assertEqual(len(req.status.details), 2)
            self.assertEqual(req.status.details[0].executor, 'DummyCrafter')
            self.assertEqual(req.status.details[1].executor, 'BaseEncoder')
            self.assertTrue(req.status.details[0].exception.startswith('ZeroDivisionError'))
            self.assertTrue(req.status.details[1].exception.startswith('NotImplementedError'))

        f = (Flow().add(name='r1', yaml_path='_forward')
             .add(name='r2', yaml_path='!DummyCrafter', replicas=3)
             .add(yaml_path='- !UnarySegmentDriver {}')
             .add(name='r3', yaml_path='!BaseEncoder'))

        with f:
            f.dry_run()

        with f:
            f.index_lines(lines=['abbcs', 'efgh'], output_fn=validate)
            f.index_lines(lines=['abbcs', 'efgh'], output_fn=validate)


if __name__ == '__main__':
    unittest.main()
